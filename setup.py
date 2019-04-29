from setuptools import find_packages
from setuptools import setup
import glob
import os

setup(name="unclean-sentiments",
      version="0.01",
      zip_safe=True,
      include_package_data=True,
      description="Cleanse some data.",
      url="darkhipo.info",
      author="Dmitri Ivanovich Arkhipov",
      author_email="dima@darkhipo.info",
      keywords="unclean, sentiment, data",
      packages=find_packages("."),
      scripts=[x for x in glob.glob("scripts/*.py")],
      data_files=[(d, [os.path.join(d,f) for f in files]) for d, folders, files in os.walk("data")] + 
      [(d, [os.path.join(d,f) for f in files]) for d, folders, files in os.walk("docs")],
      python_requires='>3,<4',
      entry_points={
          "console_scripts": ["main=main:main"]
      },
      install_requires=[ 
        "pandas",
        "sqlalchemy"
      ]
)
