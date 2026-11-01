# 改善サイクルの記録

## 保存と実行

既存のプロジェクト資料を優先する。なければ `game-evaluation/iteration-001.json` のように一サイクル一ファイルで残す。直前の受理済み記録を上書きせず、新記録と `--previous` で比較する。スキルのフォルダにゲーム固有の状態を書かない。AIが記録を作り、ユーザーに入力作業を要求しない。前回ファイルをコピーして差分だけ編集し、長いJSONを会話に再掲しない。再開時は最新記録と必要な証拠を読み、全履歴を毎回読み直さない。

```bash
python3 <skill-dir>/scripts/check_cycle.py game-evaluation/iteration-002.json --previous game-evaluation/iteration-001.json
```

標準出力はJSON。終了0は記録が規則を満たすこと、終了2は記録・作業選択の修正が必要なことを示す。面白さの証明や変更の許可にはならない。チェッカー自体は読み取り専用。人間やAIが別経路で編集することを封じるシステムではない。

この形式はSKILL.mdで改善サイクルを選んだ時に使う。通常の限定した変更は既存メモか最終報告に短く残し、初回評価JSONを必須にしない。既に関連する評価記録がある時は、その版と未解決事項を保持して更新する。分析・提案のみの依頼では回答内に記し、ファイルを生成しない。品質反復時は各判定の観測・反証・悪影響をレビューする。

## 形式 version=1

[説明用サンプル](../assets/iteration.example.json) を参照。例の観測は架空で、試遊データとして転用しない。

| フィールド | 内容 |
|---|---|
| contract | project、audience、goals（魅力の目標）、quality_floor（守る品質）、intentional_ambiguity（意図した謎）。作品ごとの契約 |
| build | 証拠の対象を一意に識別できるコミット＋変更内容ハッシュ、または配布ビルドID。変更後に同じIDを再利用しない |
| boundary | 今回確認する開始・終了・対象経路と、適用しない範囲。全編と一区間を混同しない |
| limits | minutes（時間予算）、iterations（実験数）、stall（同じ仮説で改善しない回数）。正の数、回数は整数 |
| spent | minutes、iterationsの非負の実績。開始後に都合よく減らさない |
| evidence | id、build、kind、scopes、source、observationを持つ配列。sourceはログ・動画時刻・試遊記録等の特定可能な参照 |
| assessments | aspect、scope、status、claim、evidence（証拠ID）を持つ配列。同じaspect/scopeは一つにまとめ、矛盾した結果を隠さない |
| findings | id、severity、status、aspect、observation、hypothesis、evidence。未解決事項と原因仮説 |
| history | hypothesis_id、build、outcome、evidence、note。実際に試した内容と結果を順に追加 |
| comparison | null、またはbaseline、candidate、verdict、evidence、conditions、tradeoffs。比較条件と損失も記録 |
| decision | 下表の判断 |
| next | 次の作業。終了・昇格時はnull |

### 値と意味

- evidence.kind：`runtime`（実際の実行・録画・実行経路テスト）、`human`（実際の対象プレイヤーの行動・発言）、`static`、`design`、`simulation`。作者の感想やAIの初見役をhumanにしない。データを受け取っただけなら確認範囲を明記する。
- scopes / assessment.scope：`moment`、`sequence`、`whole`。wholeはboundary内の全体であり、その外へ合格を広げない。静止画で動き・音を確認したと書かない。
- assessment.aspect：`enjoyment`、`comprehension`、`coherence`、`expression`、`function`。enjoymentは三範囲、coherenceはwhole、他は必要な範囲を最低一つ記録する。
- assessment.status：`pass`（その範囲と主張を支える現在の実証）、`fail`（反する証拠）、`unknown`（未確認・予測）、`na`（対象外の理由をclaimへ記載）。enjoymentを対象外にしない。AIによる魅力の予測はunknownのclaimへ、原因の予測はfinding.hypothesisへ記す。
- enjoyment / comprehensionのpass/failには、対象版・対象範囲のhumanが必要。その他のpass/failには対象版・対象範囲のruntimeまたはhumanが必要。古い版の不満は現在の懸念としてunknownへ残す。AIの批評はunknownと原因仮説・重要問題に反映し、人間が楽しんだ／退屈した実証と分ける。kindとscopeを宣言しただけで証拠の内容が適切になるわけではない。AIは原資料を見て確認する。
- findings.severity：`core`、`major`、`minor`。statusは`open`か`resolved`。不明点はassessment.unknownに残す。resolvedには`resolved_build`とその版の実行証拠が必要。新たに解消した時は現行版を記録する。過去の解消はそのまま保持し、関連変更で再発が疑われる時に再確認・openへ戻す。機能上の原因を解消しても楽しさが未確認なら、enjoymentはunknownのまま。
- history.outcome：`improved`、`not_improved`、`unknown`。何が改善したかnoteへ限定する。機能改善を楽しさの実証に読み替えない。改善・非改善にはそのbuildの実行証拠が必要。
- comparison.verdict：`better`、`worse`、`mixed`、`unknown`。両版の実行証拠を参照する。人間の楽しさが不明なら、改善の主張を観測できた範囲へ限定し、面白さの比較はunknownと明記する。

| decision | 意味 |
|---|---|
| iterate | 原因を検証する変更または証拠収集を続ける |
| keep_provisional | 現行版の実行で限定した改善を確認し暫定採用。未検証の楽しさや全体完成を主張しない |
| promote | boundary内の受入基準が満たされたとして次工程へ進む。全assessmentがpass/na、重大未達なし。比較があるならbetter/mixedの理由を示す |
| handoff | 予算・環境・人間確認などでこの作業を終え、再開条件と次の実験を残す |
| stop | この反復を止め、未達と理由を残す |

nextは`kind`（experiment / collect / polish）、`addresses`（問題ID配列）、`hypothesis_id`、`change`、`check_function`、`check_fun`、`check_regression`、`minutes`を持つ。check_funには予測と反証条件、人間が利用可能な場合の直接の楽しさ確認、利用不可能な場合の扱いを記す。理解の質問や結果が変わる確認だけで代用しない。minutesには実装・確認・記録を含める。

## 作業ゲート

- 最上位のopen問題を最低一つ扱う。core/majorが残る時は無関係なpolishに進まない。必要な芝居・音・UIの修正はexperimentとして該当問題に結ぶ。
- 予算を超える新作業を始めない。予算終了時はhandoff/stopにしてnext=null。完了処理で超過した実績を隠さない。
- 同じ仮説の改善なしがstallに達したら原因仮説を変えるか止める。他の仮説を間に挟んでもその仮説の停滞回数は消えない。証拠不足なら追加収集という別の検証を明示する。仮説IDの付け替えで逃げない。実質的に変える時は変更した原因・予測・反証条件をhistory.noteへ残す。
- 次工程へのpromoteを、現在の証拠の不足や重大問題が阻止する。人間の証拠がなくてもiterate/keep_provisionalで開発を続ける。
- 前回との比較では契約・範囲・上限を変えず、実績と履歴を減らさず、証拠を書き換えず、問題を消さない。findingのaspectと元のobservationは固定して別の問題へすり替えない。原因仮説の見直しは元の観測を保持し、hypothesisと履歴のnoteで記録する。元の観測の誤りが判明した場合も訂正の証拠と理由を残して解消扱いにし、新しい問題は別IDで追加する。
- 本当に契約・評価範囲を変える場合や予算を追加する場合は、ユーザーの既存の指示・許可を確認し、別の作業枠を開始する。前枠の最終記録への参照と、変更理由・承認根拠を新記録に追加し、前回結果を保存する。初回形式へ戻すことを隠れた基準緩和に使わない。

## 検証と限界

```bash
python3 -m unittest discover -s <skill-dir>/tests -v
```

このプログラムはJSON構造と宣言された関係を点検する。資料の真偽、意味的な妥当性、実際の作業時間、対象プレイヤーの代表性、魅力の強さは認証しない。通過を「面白いゲームになった」「安全に公開できる」に言い換えない。エンジン接続、自動操作、録画は利用環境で使えるものを選び、ない能力を持つように振る舞わない。
