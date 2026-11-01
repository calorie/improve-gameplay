# improve-gameplay — ゲームの面白さを磨く

AIによるゲーム開発で、対象プレイヤーにとっての面白さを中心に改善を反復するための汎用スキルです。特定のゲーム、エンジン、ジャンルや既存の `game-development` プラグインには依存しません。

## 何をするか

- ゲームが動くこと、理解できること、楽しいことを分けて評価します。
- 瞬間、一連のプレイ、対象全体で観察し、物語・遊び・UI・表現のつながりを確認します。
- 最重要の問題から原因仮説を選び、実装前後を比較します。コアが未成立のまま無関係な装飾へ進むことを抑えます。
- 作業予算、停滞、未解決問題、証拠を記録し、別のセッションでも再開できるようにします。

これは自動でゲームを操作するプログラムではありません。スキルを利用するAIと、その環境にあるエンジン・操作・録画等の道具が実行を担います。Pythonチェッカーは記録の整合性と作業選択の規則を確認します。面白さそのものを数値認定するものではありません。

## 一度インストールし、普段どおり依頼する

このリポジトリは単独のスキルです。入口は [SKILL.md](SKILL.md)。`agents/openai.yaml` の `allow_implicit_invocation: true` により、対応環境がゲーム開発の依頼から自動選択できます。毎回スキル名を指定したり、評価手順をプロンプトに書いたりする必要はありません。

ローカルのCodexでは、最初の一度だけ次のように依頼できます。

```text
$skill-installer を使って、https://github.com/calorie/improve-gameplay の
ルートにあるスキルを個人用としてインストールしてください。
```

ローカルで手動配置する場合は、このディレクトリ一式を `~/.agents/skills/improve-gameplay/` に置きます。同名スキルを既に管理している環境では、その既存のスキルを更新し、重複して配置しないでください。ChatGPT Workではスキルをインストール・有効化する機能を使います。個人用に有効化すれば、対象のゲームやセッションごとの設定追加は不要です。インストール方法と対応範囲は [OpenAIの公式ガイド](https://learn.chatgpt.com/docs/build-skills) を参照してください。

インストール後は、ゲームを読み取り・実行できる開発セッションで、例えば次のように依頼します。

```text
敵の予備動作を見て回避できるように調整して。
```

```text
救出後の会話を、直前の戦闘結果に自然につなげて。
```

```text
このゲームをもっと面白くして。今回は最大30分。
```

| 依頼 | AIの進め方 |
|---|---|
| 限定した機能追加・調整 | 狙う体験に結び付け、変更前後と関連場面を確認。既存メモか報告に短く残す |
| 全体改善・新規ゲーム・コアの修正 | 最重要の原因仮説を選び、実装・比較・採否を反復。評価記録とチェッカーを使う |
| 分析・提案のみ | 根拠と改善案を回答。ファイルを作らず、実装へ進まない |
| 誤字だけ・ビルドだけ・ゲーム以外 | ゲーム評価の手順を追加しない |

初期設定や評価JSONの入力は利用者に求めず、AIが既存資料を読み、必要な記録を作成・更新します。人間の試遊では、楽しい・退屈な瞬間、続きを遊びたいか、その理由を確認します。AIの予測だけで「人間が楽しめた」とは判定しません。

暗黙の選択は利用環境の判断に依存し、毎ターンの呼び出しを保証するものではありません。確実に指定したい場面では `$improve-gameplay` 等の明示呼び出しも使えます。常駐監視は行わず、ゲームの実行手段は利用環境が提供するものを使います。別のアクティブなセッションやその作業領域は操作対象にしません。

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
| [SKILL.md](SKILL.md) | 普段の依頼への適用、通常変更、作業範囲 |
| [references/iteration.md](references/iteration.md) | コア改善の反復、優先順位、予算、引き継ぎ |
| [references/evaluation.md](references/evaluation.md) | 面白さ・物語・全体の評価、試遊、参考文献 |
| [references/record-format.md](references/record-format.md) | 評価記録とチェッカーの規則 |
| [assets/iteration.example.json](assets/iteration.example.json) | 記録形式のサンプル |
| [scripts/check_cycle.py](scripts/check_cycle.py) | 証拠、優先順位、予算、停滞の確認 |
| [tests/test_cycle.py](tests/test_cycle.py) | チェッカーのテスト |
| [evals/validation.md](evals/validation.md) | 初版の行動検証、結果、限界 |
| [evals/implicit-usage.md](evals/implicit-usage.md) | 通常作業とコア改善の使い分けの比較検証 |

初版では35件のプログラムテストと架空資料による行動検証を行っています。実ゲームでの楽しさ向上はまだ実証していません。詳しい条件と限界は検証記録を参照してください。
