from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
import argparse
import chromedriver_binary
import json
import logging
import re
import subprocess
import sys
import yaml


# モジュールとしてロードしたとき、driverにアクセスできるようにする。
_driver = None


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)


class Configuration(object):
    def __init__(self, email, password):
        self._email = email
        self._password = password

    @property
    def email(self):
        return self._email

    @property
    def password(self):
        return self._password


class PaizaProblemMetadata(object):
    def __init__(self, challenge_id: int, problem_id: str, ready_url: str):
        self._challenge_id = challenge_id
        self._problem_id = problem_id
        self._ready_url = ready_url

    @property
    def challenge_id(self):
        return self._challenge_id

    @property
    def problem_id(self):
        return self._problem_id

    @property
    def ready_url(self):
        return self._ready_url

    def to_dict(self):
        return {
            'challenge_id': self._challenge_id,
            'problem_id': self._problem_id,
            'ready_url': self._ready_url
        }


class PaizaWorkspaceException(Exception):
    pass


def validate_ready_url(url: str):
    if not re.match(r'^https://paiza.jp/challenges/\d+/ready$', ready_url):
        raise PaizaWorkspaceException("Failed to validate ready_url.")


def get_driver():
    global _driver
    if _driver is None:
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        _driver = webdriver.Remote(options=options)
        _driver.implicitly_wait(10)
    return _driver


def test_get_problem_id_from_title_b106():
    title = 'B106:席替えの席決め'
    actual = get_problem_id_from_title(title)
    expect = 'B106'
    assert expect == actual


def test_get_problem_id_from_title_b103():
    title = '【銀の弾丸コラボ問題】B103:カブトムシの誘導の問題にチャレンジ！'
    actual = get_problem_id_from_title(title)
    expect = 'B103'
    assert expect == actual


def get_problem_id_from_title(title: str):
    m = re.search(r'([A-Z]\d+):', title)
    if not m:
        raise PaizaWorkspaceException(f"Failed to parse problem id: {title}")
    return m.group(1)


def get_challenge_id_from_ready_url(ready_url: str):
    m = re.search(r'/challenges/(\d+)/', ready_url)
    if not m:
        raise PaizaWorkspaceException(
                f"Failed to parse challenge id: {ready_url}")
    return m.group(1)


def create_metadata(title: str, ready_url: str):
    problem_id = get_problem_id_from_title(title)
    challenge_id = get_challenge_id_from_ready_url(ready_url)
    return PaizaProblemMetadata(challenge_id, problem_id, ready_url)


def scrape_and_create_metadata(ready_url: str, config: Configuration):
    validate_ready_url(ready_url)

    driver = get_driver()
    driver.get(ready_url)

    logger.error('ログインする。')
    email_form = driver.find_element(by=By.ID, value='email')
    email_form.send_keys(config.email)
    password_form = driver.find_element(by=By.ID, value='password')
    password_form.send_keys(config.password)
    submit_button = driver.find_element(
            by=By.XPATH, value="//input[@type='submit']")
    submit_button.click()

    logger.error('画面の描画を待つ。')
    timeout = 10
    wait = WebDriverWait(driver, timeout)
    wait.until(
            expected_conditions.element_to_be_clickable(
                (By.ID, 'js-challenge-problem')))

    logger.error('スクレイプしてメタデータを得る。')
    return create_metadata(driver.title, ready_url)


if __name__ == '__main__':
    logger.error('引数を解析する。')
    parser = argparse.ArgumentParser()
    parser.add_argument('url', nargs=1)
    parser.add_argument(
            '--config-file',
            default='config.yaml',
            type=argparse.FileType('r', encoding='utf-8'))
    parsed_args = parser.parse_args()
    ready_url = parsed_args.url[0]

    logger.error('設定を読む。')
    data = yaml.safe_load(parsed_args.config_file)
    config = Configuration(**data)

    try:
        logger.error('メタデータを得る。')
        metadata = scrape_and_create_metadata(ready_url, config)
    finally:
        logger.error('ドライバを終了する。')
        _driver.close()

    logger.error('ディレクトリを作る。')
    script_dir = Path(__file__).parent.resolve()
    problem_dir = script_dir / 'submit' / metadata.problem_id
    problem_dir.mkdir(parents=True, exist_ok=True)

    logger.error('ファイルを作る。')
    metadata_file = problem_dir / 'metadata.json'
    if not metadata_file.exists():
        with open(str(metadata_file), 'w') as f:
            json.dump(data, f)

    logger.error('エディタを開く。')
    code_file = problem_dir / 'Main.py'
    if not code_file.exists():
        subprocess.run(
                f'gvim -c "Template atcoder" {code_file}', shell=True)
    else:
        subprocess.run(f'gvim {code_file}', shell=True)

    logger.error('ターミナルを開く。')
    subprocess.run('powershell', cwd=str(problem_dir))
