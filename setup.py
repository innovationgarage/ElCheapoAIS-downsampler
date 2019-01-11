#!/usr/bin/env python

import setuptools

setuptools.setup(name='aisdownsampler',
      version='0.1',
      description='Streaming downsampler of NMEA AIS data',
      long_description='Streaming downsampler of NMEA AIS data',
      long_description_content_type="text/markdown",
      author='Saghar Asadi',
      author_email='saghar@innovationgarage.no',
      url='https://github.com/innovationgarage/ElCheapoAIS-aisdownsampler',
      packages=setuptools.find_packages(),
      install_requires=[
          'libais==0.17',
          'Twisted==18.9.0',
          'click',
          'click-datetime'
      ],
      include_package_data=True,
      entry_points='''
      [console_scripts]
      aisdownsampler = aisdownsampler.cli:main
      '''
  )
