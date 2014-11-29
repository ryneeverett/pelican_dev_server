import setuptools

setuptools.setup(
    name='pelican_dev_server',
    install_requires=['cherrypy', 'pelican', 'watchdog'],
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': ['pelican_dev_server=pelican_dev_server.main:main']}
)
