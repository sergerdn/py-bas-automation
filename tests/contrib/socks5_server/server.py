import logging
import select
import socket
import struct
import sys
import time
from socketserver import BaseRequestHandler, TCPServer, ThreadingMixIn

logger = logging.getLogger("[socks5-server]")
# Constants
SOCKS_VERSION = 5
CONNECT = 1
RESERVED = 0
FAILURE = 0xFF
USERNAME_PASSWORD_VERSION = 1
CONNECTION_TIMEOUT = 60 * 15 * 1000
COPY_LOOP_BUFFER_SIZE = 4096
BIND_PORT = 0  # set to 0 if we are binding an address, lets the kernel decide a free port

# Buffer sizes
GREETING_SIZE = 2
AUTH_METHOD_SIZE = 1
VERSION_SIZE = 1
ID_LEN_SIZE = 1
PW_LEN_SIZE = 1
CONN_NO_PORT_SIZE = 4
CONN_PORT_SIZE = 2
DOMAIN_SIZE = 1


class AuthMethod:
    NoAuth = 0
    GSSAPI = 1
    UsernamePassword = 2
    Invalid = 0xFF


class StatusCode:
    Success = 0
    GeneralFailure = 1
    NotAllowed = 2
    NetUnreachable = 3
    HostUnreachable = 4
    ConnRefused = 5
    TTLExpired = 6
    CommandNotSupported = 7
    AddressTypeNotSupported = 8


class AddressDataType:
    IPv4 = 1
    DomainName = 3
    IPv6 = 4


class SOCKS5ProxyServer(ThreadingMixIn, TCPServer):
    """Just the server which will process a dictionary of options and initialise the socket server"""

    def __init__(self, options):
        options = options or {}
        # Check types, if the options are valid
        if "auth" in options:
            if not isinstance(options["auth"], tuple):
                logger.error("Auth must be a tuple with 2 items (username, password) or not set")
                sys.exit()
            if len(options["auth"]) != 2:
                logger.error("Auth must be a tuple with 2 items (username, password)")
                sys.exit()
            for item in options["auth"]:
                if not isinstance(item, str):
                    logger.error("Tuple item must be a string (type str)")
                    sys.exit()
            self._auth = options["auth"]

        if "bind_address" in options:
            # This should error out if invalid
            # This allows us to parse the address given by a user on the start of the server
            bind_addr_info = socket.getaddrinfo(
                options["bind_address"],
                BIND_PORT,
                family=socket.AF_UNSPEC,
                type=socket.SOCK_STREAM,
                flags=socket.AI_PASSIVE,
            )
            if len(bind_addr_info) > 0:
                self._bind = bind_addr_info[0][4]  # Is picking first a good idea?
            else:
                logger.error("Failed to resolve bind address")
                sys.exit()

        port = int(options["port"]) if "port" in options else 1080
        host_port_tuple = (options["listen_ip"] if "listen_ip" in options else "0.0.0.0", port)
        super().__init__(host_port_tuple, SOCKS5ProxyHandler)


class SOCKS5ProxyHandler(BaseRequestHandler):
    """The handler used for a request from a client.
    Make sure _bind and _auth is set in self.server (like in SOCKS5ProxyServer) if a custom server uses this handler
    in order to use username and password authentication or use binding for the request socket
    """

    def handle(self):
        logger.info("Accepting connection from %s:%s" % self.client_address)

        # Handle the greeting
        # Greeting header
        header = self._recv(GREETING_SIZE, self._send_greeting_failure, AuthMethod.Invalid)
        version, nmethods = struct.unpack("!BB", header)
        # Only accept SOCKS5
        if version != SOCKS_VERSION:
            self._send_greeting_failure(self.auth_method)
        # We need at least one method
        if nmethods < 1:
            self._send_greeting_failure(AuthMethod.Invalid)

        # Get available methods
        methods = self._get_available_methods(nmethods)
        logger.debug(f"Received methods {methods}")

        # Accept only USERNAME/PASSWORD auth if we are asking for auth
        # Accept only no auth if we are not asking for USERNAME/PASSWORD
        if (self.auth_method and AuthMethod.UsernamePassword not in set(methods)) or (
            not self.auth_method and AuthMethod.NoAuth not in set(methods)
        ):
            self._send_greeting_failure(AuthMethod.Invalid)

        # Choose an authentication method and send it to the client
        self._send(struct.pack("!BB", SOCKS_VERSION, self.auth_method))

        # If we are asking for USERNAME/PASSWORD auth verify it
        if self.auth_method:
            self._verify_credentials()

        # Auth/greeting handled...
        logger.debug("Successfully authenticated")

        # Handle the request
        conn_buffer = self._recv(CONN_NO_PORT_SIZE, self._send_failure, StatusCode.GeneralFailure)
        version, cmd, rsv, address_type = struct.unpack("!BBBB", conn_buffer)
        # Do this so we can send an address_type in our errors
        # We don't want to send an invalid one back in an error so we will handle an invalid address type first
        # Microsocks just always sends IPv4 instead
        if address_type in [AddressDataType.IPv4, AddressDataType.IPv6, AddressDataType.DomainName]:
            self._address_type = address_type
        else:
            self._send_failure(StatusCode.AddressTypeNotSupported)

        if version != SOCKS_VERSION:
            self._send_failure(StatusCode.GeneralFailure)
        if cmd != CONNECT:  # We only support connect
            self._send_failure(StatusCode.CommandNotSupported)
        if rsv != RESERVED:  # Malformed packet
            self._send_failure(StatusCode.GeneralFailure)

        logger.debug(f"Handling request with address type: {address_type}")

        if address_type == AddressDataType.IPv4 or address_type == AddressDataType.IPv6:  # IPv4 or IPv6
            address_family = socket.AF_INET if address_type == AddressDataType.IPv4 else socket.AF_INET6
            minlen = 4 if address_type == AddressDataType.IPv4 else 16
            raw = self._recv(minlen, self._send_failure, StatusCode.GeneralFailure)  # Raw IP address bytes

            # Convert the IP address from binary to text
            try:
                address = socket.inet_ntop(address_family, raw)
            except Exception as err:
                logger.debug(f"Could not convert packed IP {raw} to string")
                logger.error(err)
                self._send_failure(StatusCode.GeneralFailure)
        elif address_type == AddressDataType.DomainName:  # Domain name
            domain_buffer = self._recv(DOMAIN_SIZE, self._send_failure, StatusCode.GeneralFailure)
            domain_length = domain_buffer[0]
            if domain_length > 255:  # Invalid
                self._send_failure(StatusCode.GeneralFailure)
            address = self._recv(domain_length, self._send_failure, StatusCode.GeneralFailure)

        port_buffer = self._recv(CONN_PORT_SIZE, self._send_failure, StatusCode.GeneralFailure)
        port = struct.unpack("!H", port_buffer)[0]

        # Translate our address and port into data from which we can create a socket connection
        try:
            remote_info = socket.getaddrinfo(
                address, port, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM, flags=socket.AI_PASSIVE
            )
            # Pick the first one returned, probably IPv6 if IPv6 is available or IPv4 if not
            # TO-DO: Try as many as possible in a loop instead of picking only the first returned
            remote_info = remote_info[0]
        except Exception as err:  # There's no suitable errorcode in RFC1928 for DNS lookup failure
            logger.error(err)
            self._send_failure(StatusCode.GeneralFailure)

        af, socktype, proto, _, sa = remote_info

        # Connect to the socket
        try:
            # Make the socket
            self._remote = socket.socket(af, socktype, proto)
            # Bind it to an IP
            if hasattr(self.server, "_bind"):
                self._remote.bind(self.server._bind)
            self._remote.connect(sa)
            bind_address = self._remote.getsockname()
            logger.info(f"Connected to {address} {port}")

            # Get the bind address and port
            addr = struct.unpack("!I", socket.inet_aton(bind_address[0]))[0]
            port = bind_address[1]
            logger.debug(f"Bind address {addr} {port}")
        except Exception as err:
            logger.error(err)
            # TO-DO: Get the actual failure code instead of giving ConnRefused each time
            self._send_failure(StatusCode.ConnRefused)

        # TO-DO: Are the BND.ADDR and BND.PORT returned correct values?
        self._send(
            struct.pack("!BBBBIH", SOCKS_VERSION, StatusCode.Success, RESERVED, AddressDataType.IPv4, addr, port)
        )

        # Run the copy loop
        self._copy_loop(self.request, self._remote)
        self._exit(True)

    @property
    def auth_method(self):
        """Gives us the authentication method we will use"""
        return AuthMethod.UsernamePassword if hasattr(self.server, "_auth") else AuthMethod.NoAuth

    def _send(self, data):
        """Convenience method to send bytes to a client"""
        return self.request.sendall(data)

    def _recv(self, bufsize, failure_method=False, code=False):
        """Convenience method to receive bytes from a client
        If bufsize is less than the size of the data received, then failure_method is called
         with code as a parameter and kills the thread
        """
        buf = self.request.recv(bufsize)
        if len(buf) < bufsize:
            if failure_method and code:
                failure_method(code)
            elif failure_method:
                failure_method()
            else:
                self._exit()  # Kill thread if we aren't calling the failure methods (they already do this)
        return buf

    def _shutdown_client(self):
        """Convenience method to shutdown and close the connection with a client"""
        self.server.shutdown_request(self.request)

    def _exit(self, dontExit=False):
        """Convenience method to exit the thread and cleanup any connections"""
        self._shutdown_client()
        if hasattr(self, "_remote"):
            # self._remote.shutdown(socket.SHUT_RDWR)
            self._remote.close()
        if not dontExit:
            sys.exit()

    def _get_available_methods(self, n):
        """Receive the methods a client supported and return them as a list"""
        methods = []
        for i in range(n):
            methods.append(ord(self._recv(AUTH_METHOD_SIZE, self._send_greeting_failure, AuthMethod.Invalid)))
        return methods

    def _verify_credentials(self):
        """Verify the credentials of a client and send a response relevant response
        and possibly close the connection + thread if unauthenticated
        """
        version = ord(self._recv(VERSION_SIZE))
        if version != USERNAME_PASSWORD_VERSION:
            logger.error("USERNAME_PASSWORD_VERSION did not match")
            self._send_authentication_failure(FAILURE)

        username_len = self._recv(ID_LEN_SIZE, self._send_authentication_failure, FAILURE)
        username = self._recv(ord(username_len), self._send_authentication_failure, FAILURE)

        password_len = self._recv(PW_LEN_SIZE, self._send_authentication_failure, FAILURE)
        password = self._recv(ord(password_len), self._send_authentication_failure, FAILURE)

        server_username, server_password = self.server._auth

        if username.decode("utf-8") == server_username and password.decode("utf-8") == server_password:
            self._send(struct.pack("!BB", USERNAME_PASSWORD_VERSION, StatusCode.Success))
            return True

        logger.error("Authentication failed")
        self._send_authentication_failure(FAILURE)

    def _send_greeting_failure(self, code):
        """Convinence method to send a failure message to a client in the greeting stage"""
        self._send(struct.pack("!BB", SOCKS_VERSION, code))
        self._exit()

    def _send_authentication_failure(self, code):
        """Convinence method to send a failure message to a client in the authentication stage"""
        self._send(struct.pack("!BB", USERNAME_PASSWORD_VERSION, code))
        self._exit()

    def _send_failure(self, code):
        """Convinence method to send a failure message to a client in the socket stage"""
        address_type = self._address_type if hasattr(self, "_address_type") else AddressDataType.IPv4
        self._send(struct.pack("!BBBBIH", SOCKS_VERSION, code, RESERVED, address_type, 0, 0))
        self._exit()

    def _copy_loop(self, client, remote):
        """Waits for network activity and forwards it to the other connection"""
        while True:
            # Wait until client or remote is available for read
            #
            # Alternatively use poll() instead of select() due to these reasons
            # https://github.com/rofl0r/microsocks/commit/31557857ccce5e4fdd2cfdae7ab640d589aa2b41
            # May not be ideal for a cross platform implementation however
            r, w, e = select.select([client, remote], [], [], CONNECTION_TIMEOUT)

            # Kill inactive/unused connections
            if not r and not w and not e:
                self._send_failure(StatusCode.TTLExpired)

            for sock in r:
                try:
                    data = sock.recv(COPY_LOOP_BUFFER_SIZE)
                except Exception as err:
                    logger.debug("Copy loop failed to read")
                    logger.error(err)
                    return

                if not data or len(data) <= 0:
                    return

                outfd = remote if sock is client else client
                try:
                    outfd.sendall(data)  # Python has its own sendall implemented
                except Exception as exc:
                    logger.debug("Copy loop failed to send all data")
                    logger.error(exc)
                    return


if __name__ == "__main__":
    import threading

    import httpx

    logging.basicConfig(level=logging.DEBUG)

    server = SOCKS5ProxyServer(
        {
            "auth": ("username", "password"),
            "listen_ip": "127.0.0.1",
            "port": 1080,
            "bind_address": "0.0.0.0",
        }
    )

    def run_server(s) -> None:
        print("Starting server")
        s.serve_forever()

    p = threading.Thread(
        target=run_server,
        name="socks5-server",
        args=[
            server,
        ],
    )
    p.start()
    proxies = {"all://": "socks5://username:password@127.0.0.1:1080"}

    time.sleep(1)

    try:
        response = httpx.get(url="https://lumtest.com/echo.json", proxies=proxies)
        print(response.content)
        print(response.status_code)
        print(response.headers)
    finally:
        print("Killing background process")
        server.shutdown()
        p.join()
