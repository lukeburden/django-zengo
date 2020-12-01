from setuptools import find_packages, setup


name = "django-zengo"
description = "Integrate Zendesk Support and your Django app"
author = "Luke Burden"
author_email = "lukeburden@gmail.com"
url = "https://github.com/lukeburden/django-zengo"

with open("README.md", "r") as fh:
    long_description = fh.read()

install_requires = [
    "django>=2,<4",
    "zenpy>=2.0.11,<3",
    "django-konst>=2,<3",
]

tests_require = [
    "pytest>=4,<5",
    "pytest-django>=3,<4",
    "pytest-mock>=1,<2",
    "model_mommy>=1,<2"
]

setup(
    name=name,
    author=author,
    author_email=author_email,
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    version="2.0.3",
    license="MIT",
    url=url,
    packages=find_packages(exclude=["tests", "testproj"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Framework :: Django",
    ],
    install_requires=install_requires,
    test_suite="runtests.runtests",
    tests_require=tests_require,
    zip_safe=False,
)
