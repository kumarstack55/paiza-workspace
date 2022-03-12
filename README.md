# paiza-workspace

## このリポジトリについて

paiza のコードをローカルで編集するためのツールです。
指定URLをもとに問題IDごとにディレクトリを作り、
そのディレクトリでファイルの編集を試みます。

## 要件

* Python3.9+
* Poetry 1.1.7+

## 初回インストール方法

```powershell
# クローンする。
cd $HOME\Documents
gh clone https://github.com/kumarstack55/paiza-workspace.git

# PaizaにログインするIDとパスワードを設定する。
Copy-Item config.yaml.sample config.yaml
gvim config.yaml
```

## 利用方法

まず、URLから問題IDをスクレイプするために Chrome を起動します。

```powershell
docker run -d -p 4444:4444 -p 7900:7900 --shm-size="2g" selenium/standalone-chrome:4.1.2-20220217
```

次に、URLを指定して実行します。

```powershell
# D205:燃費の良さのURLを指定して実行する。
poetry run python3 start_problem.py https://paiza.jp/challenges/522/ready
```

すると submit/D205 ディレクトリが作られ、エディタが開きます。

以上
