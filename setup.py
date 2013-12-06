import os
from distutils.core import setup


r_file = open(os.path.join(os.path.dirname(__file__), 'README.rst'))
readme = r_file.read()
r_file.close()

setup(name='majormajor',
      version='0.1.0',
      description='Collaborative Document Editing Library',
      author='Ritchie Wilson',
      author_email='rawilson52@gmail.com',
      url="http://www.majormajor.org",
      long_description=readme,
      packages=["majormajor",
                "majormajor.hazards",
                "majormajor.ops"],
      license="GPLv3"
      )
