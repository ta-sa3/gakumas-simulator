import itertools
import streamlit as st

# --- 定数・マスターデータ定義 ---
# コスト定義（Wikiの基準に準拠）
COST_TABLE = {
    "低銀": 30,
    "低銀+": 39,
    "高銀": 45,
    "高銀+": 60,
    "低金": 75,
    "低金+": 102,
    "高金": 105,
    "高金+": 141,
    "虹": 150,
    "虹+": 204,
    "サポカ": 96,
    "サポカ+": 126,
}

# 評価ランクごとのコスト箱（下限, 上限）
RANK_BOXES = {
    "B": (306, 363),
    "B+": (306, 423),
    "A": (441, 519),
    "A+": (441, 594),
    "S": (546, 642),
    "S+": (546, 741),
    "SS": (651, 804),
    "SS+": (651, 858),
    "SSS": (546, 858),
    "SSS+": (546, 858),
}


def calculate_valid_combinations(cards, rank):
  """取得したカードのプールから、コスト箱と抽選ルールに合致する

  最大枚数の組み合わせパターンを全探索する
  """
  if rank not in RANK_BOXES:
    return [], "無効な評価ランクです"

  box_min, box_max = RANK_BOXES[rank]

  # カードのインデックスを用いて組み合わせを探索（重複を考慮するためcardsはオブジェクトのリスト）
  # 枚数は最大6枚（メモリーに選ばれる最大数）まで
  n = len(cards)
  max_select = min(6, n)

  valid_combinations = []

  # 1枚から最大選択枚数までの組み合わせを全探索
  for r in range(1, max_select + 1):
    for combo in itertools.combinations(cards, r):
      total_cost = sum([c["cost"] for c in combo])

      # 条件①・②: コスト下限 <= 合計コスト <= コスト上限
      if box_min <= total_cost <= box_max:
        valid_combinations.append({"combo": combo, "cost": total_cost, "size": r})

  if not valid_combinations:
    # 条件④の救済（全組み合わせが下限未満の場合、下限に最も近い最大値の組み合わせを探す）
    all_combos = []
    for r in range(1, max_select + 1):
      for combo in itertools.combinations(cards, r):
        total_cost = sum([c["cost"] for c in combo])
        all_combos.append({"combo": combo, "cost": total_cost, "size": r})

    if all_combos:
      # 上限を超えないものの中で、コストが最大、かつ枚数が最大のものを探す
      filtered = [c for c in all_combos if c["cost"] <= box_max]
      if filtered:
        max_cost = max([c["cost"] for c in filtered])
        max_cost_combos = [c for c in filtered if c["cost"] == max_cost]
        max_size = max([c["size"] for c in max_cost_combos])
        valid_combinations = [
            c for c in max_cost_combos if c["size"] == max_size
        ]

  if not valid_combinations:
    return [], "条件を満たす有効なカードの組み合わせが見つかりませんでした。"

  # 条件③: より多くの枚数（最大サイズ）で抽選される組み合わせに絞る
  max_found_size = max([c["size"] for c in valid_combinations])
  final_valid = [c for c in valid_combinations if c["size"] == max_found_size]

  return final_valid, None


# --- Streamlit UI 構築 ---
st.set_page_config(
    page_title="学マス コンテストメモリー抽選シミュレーター", layout="wide"
)

st.title("🎓 学園アイドルマスター メモリ抽選シミュレーター")
st.markdown(
    "取得したスキルカードのコストと評価ランクから、コンテストメモリーに抽選される"
    "可能性のある組み合わせを計算します。"
)

# サイドバー：育成条件の設定
st.sidebar.header("📋 育成条件設定")
selected_rank = st.sidebar.selectbox(
    "評価ランク",
    options=list(RANK_BOXES.keys()),
    index=list(RANK_BOXES.keys()).index("SSS"),
)

box_min, box_max = RANK_BOXES[selected_rank]
st.sidebar.info(
    f"選択中の箱 (コスト範囲): **{box_min} 〜 {box_max}**"
)

# メイン画面：カードプールの入力
st.header("🎴 シナリオ中で取得したスキルカード一覧")
st.markdown(
    "育成中に獲得したカードプール（候補）を追加してください。"
)

if "user_cards" not in st.session_state:
  st.session_state.user_cards = [
      {"name": "虹スキル例 (例: 決意)", "type": "虹", "cost": 150},
      {"name": "高金+スキル例", "type": "高金+", "cost": 141},
      {"name": "低銀スキル例", "type": "低銀", "cost": 30},
      {"name": "サポカ+スキル例", "type": "サポカ+", "cost": 126},
  ]

# カード追加フォーム
with st.form("add_card_form"):
  col1, col2, col3 = st.columns([3, 2, 1])
  with col1:
    c_name = st.text_input("カード名", value="新しいカード")
  with col2:
    c_type = st.selectbox("コスト種別", options=list(COST_TABLE.keys()))
  with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    add_btn = st.form_submit_button("＋ カード追加")

  if add_btn:
    st.session_state.user_cards.append(
        {"name": c_name, "type": c_type, "cost": COST_TABLE[c_type]}
    )
    st.rerun()

# 登録済みカードの一覧表示と削除
st.subheader("登録されたカードプール (合計: %d枚)" % len(st.session_state.user_cards))

if st.session_state.user_cards:
  cards_to_delete = []
  for i, card in enumerate(st.session_state.user_cards):
    col_a, col_b, col_c = st.columns([4, 2, 1])
    with col_a:
      st.text(f"{i+1}. {card['name']}")
    with col_b:
      st.text(f"種類: {card['type']} (コスト: {card['cost']})")
    with col_c:
      if st.button("削除", key=f"del_{i}"):
        cards_to_delete.append(i)

  if cards_to_delete:
    for idx in sorted(cards_to_delete, reverse=True):
      st.session_state.user_cards.pop(idx)
    st.rerun()

  if st.button("🔄 カードリストを初期化"):
    st.session_state.user_cards = []
    st.rerun()

# --- シミュレーション実行 ---
st.markdown("---")
st.header("🎯 抽選シミュレーション結果")

if st.button("▶ 抽選パターンを計算する", type="primary"):
  if not st.session_state.user_cards:
    st.warning("カードが1枚も登録されていません。カードを追加してください。")
  else:
    results, err = calculate_valid_combinations(
        st.session_state.user_cards, selected_rank
    )

    if err:
      st.error(err)
    else:
      st.success(
          f"条件に合致する抽選パターンが **{len(results)}通り** 見つかりました！"
      )

      # 確定しているカード（すべての有効パターンに共通して含まれるカード）の割り出し
      if results:
        all_combos_sets = [set(id(c) for c in r["combo"]) for r in results]
        common_set = set.intersection(*all_combos_sets)
        guaranteed_cards = [
            c for c in st.session_state.user_cards if id(c) in common_set
        ]

        if guaranteed_cards:
          st.markdown("### 🔒 確定継承されるカード（ブレなし）")
          for gc in guaranteed_cards:
            st.markdown(f"- **{gc['name']}** ({gc['type']} / コスト:{gc['cost']})")
        else:
          st.info(
              "すべてのパターンで共通して入る「完全確定カード」はありません（確率でブレます）。"
          )

      st.markdown("### 📋 抽選される可能性のある組み合わせ一覧")
      for idx, res in enumerate(results):
        combo_names = ", ".join([f"{c['name']} ({c['type']})" for c in res["combo"]])
        st.write(
            f"**パターン {idx+1}** (選択枚数: {res['size']}枚 | 合計コスト: **{res['cost']}**)"
        )
        st.markdown(f"↳ 抽出カード: {combo_names}")