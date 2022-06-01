import pickle
import os
import logging

import pdftotext

logger = logging.getLogger(__name__)


def paper_id_to_file_name(metadata_dict):
    version = metadata_dict['versions'][-1]['version']
    paper_id = metadata_dict['id']
    if paper_id.startswith('cs'):
        pdf_filename = paper_id.split('/')[1] + version + '.pdf'
    else:
        pdf_filename = metadata_dict['id'] + version + '.pdf'
    return pdf_filename


def convert_pdf_to_text_pkl(paper_pdf_path, full_text_file_path):
    with open(os.path.join(paper_pdf_path), 'rb') as file:
        try:
            paper_pdf = pdftotext.PDF(file)
        except Exception as e:
            logger.error('Could not read {}'.format(paper_pdf_path))
            logger.error(e, exc_info=True)
            paper_pdf = ['']

    with open(full_text_file_path, 'wb') as file:
        pickle.dump(list(paper_pdf), file)
