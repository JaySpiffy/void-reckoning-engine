from setuptools import setup, find_packages

setup(
    name="multi-universe-simulator",
    version="0.1.0",
    packages=find_packages(),
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'sim-engine=src.cli:main',
        ],
    },
    author="Strategy Engine Development Team",
    description="A high-fidelity Grand Strategy Campaign Engine supporting parallel simulation across multiple science fiction universes.",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    include_package_data=True,
)
