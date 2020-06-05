from setuptools import setup, find_packages
PACKAGES = find_packages()

opts = dict(name="ari6",
            maintainer="uremom",
            maintainer_email="woobreezy@gmail.com",
            description="ari6",
            long_description="ari6",
            url="https://github.com/kenneththomas/ari6",
            download_url="https://github.com/kenneththomas/ari6",
            license="MIT",
            packages=PACKAGES)


if __name__ == '__main__':
    setup(**opts)