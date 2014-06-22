from setuptools import setup, find_packages

setup(
    name='Foreman Forensics',
    version='0.0.1',
    packages=find_packages(),
    scripts=['run_foreman.py'],
    url='http://foreman-forensics.org',
    license='GPL 3.0',
    author='Sarah Holmes',
    author_email='sarah@foreman-forensics.org',
    description='Open Source Forensic Case Management',
    include_package_data=True,
    zip_safe=False,
    install_requires=["simplejson",
                      "FormEncode==1.3.0a1",
                      "Mako==0.9.1",
                      "SQLAlchemy==0.9.1",
                      "Werkzeug==0.9.4",
                      "pil==1.1.7",
                      "qrcode==4.0.4"]
)
