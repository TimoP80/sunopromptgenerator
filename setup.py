from setuptools import setup, find_packages

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='SunoPromptGenerator',
    version='1.0.0',
    author='T. Pitkänen',
    author_email='timbor@saunagames.fi',
    description='An AI-driven tool that analyzes any audio file to generate detailed prompts for Suno AI.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/TimborSaunagames/Suno-Prompt-Generator',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask==2.0.3',
        'flask-cors==3.0.10',
        'librosa==0.10.2',
        'numpy==1.26.2',
        'soundfile==0.12.1',
        'werkzeug==2.0.3',
        'py-cpuinfo==9.0.0',
        'demucs==4.0.1',
        'numba==0.59.1',
        'waitress==2.1.2',
        'click==7.1.2',
        'openai-whisper',
        # torch is excluded, user must install it manually
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
)