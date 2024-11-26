from setuptools import setup, find_packages

setup(
    name='QuickLinksDashboard',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'customtkinter',
        'pystray',
        'Pillow',
        'playwright',
        'plyer',
        'python-dotenv'
    ],
    entry_points={
        'console_scripts': [
            'quicklinks-dashboard=core.Core:main',
        ],
    },
    author='Your Name',
    author_email='your.email@example.com',
    description='A GUI application for quick access to internal tools and dashboards.',
    url='https://github.com/yourusername/quick-links-dashboard',
) 