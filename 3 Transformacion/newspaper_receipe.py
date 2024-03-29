import argparse
import logging
import hashlib
import nltk
import pandas as pd
from urllib.parse import urlparse
from nltk.corpus import stopwords

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pd.options.display.max_rows = 999

stop_words = set(stopwords.words('spanish'))

def main(filename):
    logger.info('Staring cleaning process')

    df = _read_data(filename)
    newspaper_uid = _extract_newspaper_uid(filename)
    df = _add_newspaper_uid_column(df, newspaper_uid)
    df = _extract_host(df)
    df = _add_missing_titles(df)
    df = _generate_uids_for_rows(df)
    df = _remove_new_lines_from_body(df)
    df['n_tokens_title'] = _token_size_column(df, 'title')
    df['n_tokens_body'] = _token_size_column(df, 'body')
    df = _remove_duplicate_entries(df, 'title')
    df = _drop_rows_missing_data(df)
    _save_data(df, filename)

    return df


def _read_data(filename):
    logger.info(f'Reading file {filename}')
    return pd.read_csv(filename, encoding='ISO-8859-1')

def _extract_newspaper_uid(filename):
    logger.info('Extracting newspaper_uid')
    newspaper_uid = filename.split('_')[0]
    logger.info(f'News paper uid detected: {newspaper_uid}')
    return newspaper_uid

def _add_newspaper_uid_column(df, newspaper_uid):
    logger.info(f'Adding column "newspaper_uid" with: {newspaper_uid}')
    df['newspaper_uid'] = newspaper_uid
    logger.info('Added column')
    return df

def _extract_host(df):
    logger.info('Extracting host from urls')
    df['host'] = df['url'].apply(lambda url: urlparse(url).netloc)
    logger.info('Extracted hosts')
    return df

def _add_missing_titles(df):
    logger.info(f'Filling missing titles')
    missing_titles_mask = df['title'].isna()
    missing_titles = (df[missing_titles_mask]['url']
                        .str.extract(r'(?P<missing_titles>[^/]+)$')    
                        .applymap(lambda title: title.split('-'))
                        .applymap(lambda title_word_list: ' '.join(title_word_list))                                                  
    )

    df.loc[missing_titles_mask, 'title'] = missing_titles.loc[:, 'missing_titles']
    return df

def _generate_uids_for_rows(df):
    logger.info('Generating uids for each row')
    uids = (df
            .apply(lambda row: hashlib.md5(bytes(row['url'].encode('ISO-8859-1'))), axis=1)
            .apply(lambda hash_object: hash_object.hexdigest())
            )
    df['uid'] = uids
    return df.set_index('uid')

def _remove_new_lines_from_body(df):
    logger.info('Remove new lines from body')
    stripped_body = (df
                     .apply(lambda row: row['body'], axis=1)
                     .apply(lambda body: list(body))
                     .apply(lambda letters: list(map(lambda letter: letter.replace('\n', ' '), letters)))
                     .apply(lambda letters: list(map(lambda letter: letter.replace('\r', ' '), letters)))
                     .apply(lambda letters: ''.join(letters))
                    )
    df['body'] = stripped_body
    return df

def _token_size_column(df, column_name):
    logger.info(f'Conting relevant words of each {column_name}')
    return (df
            .dropna()
            .apply(lambda row: nltk.word_tokenize(row[column_name]), axis=1)
            .apply(lambda tokens: list(filter(lambda token: token.isalpha(), tokens)))
            .apply(lambda tokens: list(map(lambda token: token.lower(), tokens)))
            .apply(lambda word_list: list(filter(lambda word: word not in stop_words, word_list)))
            .apply(lambda valid_word_list: len(valid_word_list))
            )

def _remove_duplicate_entries(df, column_name):
    logger.info(f'Removing duplicate entries in {column_name}')
    df.drop_duplicates(subset=column_name, keep='first', inplace=True)
    return df

def _drop_rows_missing_data(df):
    logger.info('Dropping rows with missing data')
    return df.dropna()

def _save_data(df, filename):
    clean_file = f'clean_{filename}'
    logger.info(f'Saving data at location: {filename}')
    df.to_csv(clean_file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename',
                        help='The path to the dirty data',
                        type=str)
    args = parser.parse_args()
    data_frame = main(args.filename)
    print(data_frame)