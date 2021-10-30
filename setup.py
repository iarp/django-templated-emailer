from setuptools import setup

setup(
    name='django-templated-emailer',
    version='0.5',
    description='An Email template and queue system I use in many django projects.',
    url='',
    author='IARP',
    author_email='iarp.opensource@gmail.com',
    license='MIT',
    packages=['django_templated_emailer'],
    install_requires=["django>=1.11", "requests"],
    zip_safe=False
)
