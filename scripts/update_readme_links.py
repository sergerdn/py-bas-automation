"""
Adopted from https://gist.github.com/TkTech/29d8fd346c941c981752595b202ac75d
"""

import codecs

import humanmark
from urllib.parse import urljoin
import os

PROJECT_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../"))
DIST_FOLDER = os.path.join(PROJECT_PATH, "dist")


def update_readme_links(readme_path, target_readme_path, base_url, image_base_url):
    with codecs.open(readme_path, 'r', encoding='utf-8') as f:
        doc = humanmark.load(f)

    print("Readme content has been loaded.")

    links = doc.find(
        # Only find link nodes
        humanmark.ast.Link,
        # We don't want to rewrite links that use a reference
        f=lambda l: l.reference is None,
        # A negative value means to search the entire tree.
        depth=-1
    )

    for link in links:
        if link.url.startswith("http://") or link.url.startswith("https://"):
            continue

        old_url = str(link.url)
        link.url = urljoin(base_url, link.url)

        print(f"Updating link from: {old_url}, to: {link.url}")

    img_links = doc.find(
        # Only find link nodes
        humanmark.ast.Image,
        # We don't want to rewrite links that use a reference
        f=lambda l: l.reference is None,
        # A negative value means to search the entire tree.
        depth=-1
    )

    for link in img_links:
        if link.url.startswith("http://") or link.url.startswith("https://"):
            continue

        old_url = str(link.url)
        link.url = urljoin(image_base_url, link.url)
        link.url = link.url.replace("/docs/images/", "/images/")

        print(f"Updating image link from: {old_url}, to: {link.url}")

    with codecs.open(target_readme_path, 'w', encoding='utf-8') as f:
        humanmark.dump(doc, f)


def main():
    if not os.path.exists(DIST_FOLDER):
        os.makedirs(DIST_FOLDER)

    base_url = "https://github.com/sergerdn/py-bas-automation/blob/develop/"
    # https://raw.githubusercontent.com/greyli/flask-share/master/images/demo.png
    image_base_url = "https://sergerdn.github.io/py-bas-automation/"

    readme_path = os.path.join(os.path.dirname(__file__), "../README.md")
    target_readme_path = os.path.join(DIST_FOLDER, "README.md")
    update_readme_links(readme_path, target_readme_path, base_url, image_base_url)

    print("README links have been updated.")


if __name__ == "__main__":
    main()
