# mrsaweb

# MRSA Sequence Uploader
MRSA Sequence Uploader is a platform that allows researchers to upload sequence data of MRSA bacteria to a public repository. There are two ways to upload the sequence data one is this website and the other on the command line. You can use it to upload the genomes of MRSA samples to make them publicly and freely available to other researchers.

The uploader uses the Arvados Cloud platform for managing, processing, and sharing genomic and other large scientific and biomedical data. The Arvados instance was deployed on KAUST servers for testing and development.

## Using Web portal for uploading

For uploading the sequence data through [web portal](https://mrsa.cborg.cbrc.kaust.edu.sa/upload/), You can follow the following steps:

1. You will need to sign in if you have already registered. You can sign in using your ORCID account to by clicking on **Orcid.org** link on sign in page.
2. Once you are logged in, click on the **Upload** menu from top menu bar.
3. Choose the two sequence read files to be uploaded and metadata file (or fill the input fields in the form) from the file system and submit the form. It will take few minutes to upload and process sequence file. 

**Note** that if the metadata file is not selected, then the metadata required fields in the form must be filled in order to submit data. 

4. Once the data is processed, click on the **Submissions** menu from the menu bar to see your list of submissions.
5. Click on the view link to see the details your submitted data.
6. The ID in submission details page is the URL to the sequence data directory in the Arvados. Click on the URL to see the submitted data.
7. You can download and view uploaded files on arvados web interface.

## Installatin commandline tool
To get started, you need to install the uploader first and then run the main.py script in uploader directory.

1. **Download.** You can download the uploader by cloning the github repository using following command:

```sh
git clone https://github.com/bio-ontology-research-group/mrsa-sequences.git
```

2. **Prepare your system.** You need to make sure you have Python, and the ability to install modules such as `pycurl` and `pyopenssl`. On Ubuntu 18.04, you can run:

```sh
sudo apt update
sudo apt install -y virtualenv git libcurl4-openssl-dev build-essential python3-dev libssl-dev
```
3. **Create and enter your virtualenv.** Go to downloaded uploader directory and make and enter a virtualenv:

```sh
virtualenv --python python3 venv
. venv/bin/activate
```
Note that you will need to repeat the `. venv/bin/activate` step from this directory to enter your virtualenv whenever you want to use the installed tool.

4. **Install the dependencies.** Once the virtualenv is setup, install the dependencies:

```sh
pip install -r requirements.txt
```

5. **Test the tool.** Try running:

```sh
python uploader/main.py --help
```

6. **Set Arvados API Token.** Before uploading the sequence files, you need to set arvados api token value to environment variable ARVADOS_API_TOKEN. It will look something as the following:
```sh
export ARVADOS_API_TOKEN=2jv9346o396exampledonotuseexampledonotuseexes7j1ld
```

You can find the arvados token at [current token link](https://workbench.cborg.cbrc.kaust.edu.sa/current_token) in your user profile menu on [arvados web portal](https://workbench.cborg.cbrc.kaust.edu.sa/).

# Usage

Run the uploader with a FASTA or FASTQ reads gzipped files and accompanying metadata file in YAML:

```sh
python uploader/main.py reads1.fastq.gz reads2.fastq.gz metadata.yaml
```

You can find the example files on mrsa [web uploader](https://mrsa.cborg.cbrc.kaust.edu.sa/upload/). Here are the links to example files:

- Example [fastq read file 1](https://mrsa.cborg.cbrc.kaust.edu.sa/static/reads1.fastq.gz)
- Example [fastq read file 2](https://mrsa.cborg.cbrc.kaust.edu.sa/static/reads2.fastq.gz)
- Example [Metadata file](https://mrsa.cborg.cbrc.kaust.edu.sa/static/metadata.yaml)

Once the sequence is uploaded, you can see the status of the job in state.json file.