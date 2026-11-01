# improve-gameplay — ゲームの面白さを磨く

AIによるゲーム開発で、対象プレイヤーにとっての面白さを中心に改善を反復するための汎用スキルです。特定のゲーム、エンジン、ジャンルや既存の `game-development` プラグインには依存しません。

## 何をするか

- ゲームが動くこと、理解できること、楽しいことを分けて評価します。
- 瞬間、一連のプレイ、対象全体で観察し、物語・遊び・UI・表現のつながりを確認します。
- 最重要の問題から原因仮説を選び、実装前後を比較します。コアが未成立のまま無関係な装飾へ進むことを抑えます。
- 作業予算、停滞、未解決問題、証拠を記録し、別のセッションでも再開できるようにします。

これは自動でゲームを操作するプログラムではありません。スキルを利用するAIと、その環境にあるエンジン・操作・録画等の道具が実行を担います。Pythonチェッカーは記録の整合性と作業選択の規則を確認します。面白さそのものを数値認定するものではありません。

## 使う

スキルを利用できる環境に、このディレクトリを `improve-gameplay` として配置・登録してください。入口は [SKILL.md](SKILL.md) です。`agents/openai.yaml` は暗黙の呼び出しを無効にしています。

ゲームを読み取り・実行できる開発セッションで、明示して依頼します。

```text
$improve-gameplay を使って、このゲームを改善してください。
対象プレイヤーと狙う魅力を既存資料から整理し、全体を評価して、
最も重要な問題から改善・実行・比較してください。
今回は最大30分・3実験。評価履歴はプロジェクトに保存してください。
面白さの予測と人間が実際に楽しんだ証拠は区別してください。
```

上記の呼び出し表記に対応しない環境では、利用中のアプリのスキル選択機能で本スキルを選び、同じ依頼を渡します。別のアクティブなセッションやその作業領域は操作対象にしません。

AIが評価記録を作成・更新します。利用者が毎回JSONを手で埋める必要はありません。再開時は、対象プロジェクトと最新の評価記録を指定してください。人間の試遊ができる場合は、楽しい・退屈な瞬間、続きを遊びたいか、その理由を伝えます。

## 記録の検証

Python 3と標準ライブラリを使います。リポジトリのルートで実行します。

```bash
# 説明用サンプルの確認
python3 scripts/check_cycle.py assets/iteration.example.json

# プロジェクト側に保存した記録の確認
python3 scripts/check_cycle.py /path/to/game/game-evaluation/iteration-002.json \
  --previous /path/to/game/game-evaluation/iteration-001.json

# チェッカーのテスト
python3 -m unittest discover -s tests -v

# 同梱の架空事例で引き継ぎ記録を確認
python3 scripts/check_cycle.py evals/iteration-002.json --previous evals/iteration-001.json
```

初回の記録では `--previous` を省略します。終了コード0は記録の規則を満たすことを示し、ゲームの面白さや観測内容の真実性を保証しません。

## 構成

| 場所 | 内容 |
|---|---|
| [SKILL.md](SKILL.md) | 開始、評価、改善、引き継ぎの手順 |
| [references/evaluation.md](references/evaluation.md) | 面白さ・物語・全体の評価、試遊、参考文献 |
| [references/record-format.md](references/record-format.md) | 評価記録とチェッカーの規則 |
| [assets/iteration.example.json](assets/iteration.example.json) | 記録形式のサンプル |
| [scripts/check_cycle.py](scripts/check_cycle.py) | 証拠、優先順位、予算、停滞の確認 |
| [tests/test_cycle.py](tests/test_cycle.py) | チェッカーのテスト |
| [evals/validation.md](evals/validation.md) | 初版の行動検証、結果、限界 |

初版では35件のプログラムテストと架空資料による行動検証を行っています。実ゲームでの楽しさ向上はまだ実証していません。詳しい条件と限界は検証記録を参照してください。
