import argparse
import logging
import pandas as pd
from article import Article
from base import Base, engine, Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(filename):
    Base.metadata.create_all(engine)
    session = Session()
    articles = pd.read_csv(filename, encoding='ISO-8859-1')

    for index, row in articles.iterrows():
        logger.info('Loading article uid {} into DB'.format(row['uid']))
        article = Article(row['uid'],
                          row['body'],
                          row['host'],
                          row['newspaper_uid'],
                          row['n_tokens_body'],
                          row['n_tokens_title'],
                          row['title'],
                          row['url']
                         )

        session.add(article)
        session.commit()
        session.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', 
                         help='The file you want to load into th DataBase',
                         type=str)

    args = parser.parse_args()
    main(args.filename)