from setuptools import setup
from codecs import open
from os import path

# here = path.abspath(path.dirname(__file__))
#
# long_description = ''
# with open(path.join(here, 'README.md'), encoding='utf-8') as f:
#     for line in f:
#         if line.startswith('## Sample'):
#             break
#         long_description += line

setup(
    name="acmi",
    version='0.2.0',
    description="An ACMI flight record file parser",
    long_description="ACMI is a file used by tacview for creating flight recording from simulators or real world.",
    url='https://github.com/rp-/acmi',
    author="Peinthor Rene",
    author_email="peinthor@gmail.com",
    license="LGPLv3",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Games/Entertainment :: Simulation',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3 :: Only'
    ],
    keywords='acmi tacview',
    # install_requires=['pydcs'],
    packages=['acmi'],
    # package_data={
    #     'dcs/terrain': ['caucasus.p', 'nevada.p']
    # },
    # entry_points={
    #     'console_scripts': [
    #         'dcs_random=dcs.scripts.random_mission:main',
    #         'dcs_dogfight_wwii=dcs.scripts.dogfight_wwii:main',
    #         'dcs_oil_convoy=dcs.scripts.destroy_oil_transport'
    #     ]
    # },
    # test_suite="tests"
)
