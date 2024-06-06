from setuptools import setup, find_packages

setup(
    name='django-templated-emailer',
    version='0.5',
    description='An Email template and queue system I use in many django projects.',
    url='',
    author='IARP',
    author_email='iarp.opensource@gmail.com',
    license='MIT',
    packages=find_packages(),
    install_requires=["django>=1.11", "requests", "celery"],
    zip_safe=False
)
