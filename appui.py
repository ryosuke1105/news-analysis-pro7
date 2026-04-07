import streamlit as st
import feedparser
import pandas as pd
import datetime
import re

# --- 1. ページ設定とプロフェッショナル・スタイル ---
st.set_page_config(page_title="News Intelligence Pro", page_icon="📰", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetric"] {
        background-color: #ffffff !important; 
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #eef0f2;
    }
    [data-testid="stMetric"] label, 
    [data-testid="stMetric"] [data-testid="stMetricValue"] > div {
        color: #31333f !important;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
        font-weight: bold;
    }
    .stLinkButton>a {
        width: 100%;
        border-radius: 5px;
        background-color: #f0f2f6;
        color: #31333F !important;
        border: 1px solid #dcdfe3;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-weight: bold;
        padding: 0.5em 0;
    }
    .stLinkButton>a:hover {
        border-color: #007bff;
        color: #007bff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. パスワード認証機能 ---
def check_password():
    if "failed_attempts" not in st.session_state:
        st.session_state["failed_attempts"] = 0
    if st.session_state["failed_attempts"] >= 3:
        st.error("🚨 セキュリティロック: パスワードを複数回間違えたため、アクセスが遮断されました。管理者に連絡してください。")
        return False
    if "password_correct" not in st.session_state:
        st.markdown("### 🔐 システムアクセス")
        remaining = 3 - st.session_state["failed_attempts"]
        st.warning(f"注意：あと {remaining} 回間違えるとロックされます。")
        pwd_input = st.text_input("🔑 合言葉（パスワード）", type="password")
        if st.button("ログイン"):
            if pwd_input == "THEEMICHELLEGUNELEPHANT": 
                st.session_state["password_correct"] = True
                st.session_state["failed_attempts"] = 0 
                st.rerun()
            else:
                st.session_state["failed_attempts"] += 1
                st.error(f"合言葉が違います。（失敗回数: {st.session_state['failed_attempts']}/3）")
                st.rerun()
        return False
    return True

# --- 3. メインアプリケーション ---
if check_password():
    with st.sidebar:
        st.title("⚙️ 検索・分析設定")
        
        # 【変更ポイント】カレンダーが上に開いても切れないように、他の項目を先に配置します
        st.info("💡 **分析プロトコル**\n・ノイズ除去：フル稼働中")
        keyword = st.text_input("検索キーワード", "北九州 ニュース")
        max_results = st.slider("最大取得件数", 10, 100, 50)
        
        st.markdown("<br>", unsafe_allow_html=True) # 少し余白を入れて見やすくします
        
        # カレンダーをサイドバーの中段に配置
        today = datetime.date.today()
        date_range = st.date_input("分析期間", value=(today - datetime.timedelta(days=7), today), max_value=today)
        
        st.divider()
        start_button = st.button("🚀 分析を開始する")
        feedback_url = "https://docs.google.com/forms/d/e/1FAIpQLSc43_pvBP5SgbHIvLe-v0os4toA04Gd9od0IR5D5w8t--Z55w/viewform?usp=publish-editor"
        st.write("") 
        st.link_button("📋 開発へのフィードバックを送る", feedback_url, use_container_width=True)

        # 念のため下部の余白も残しておきます
        st.markdown('<div style="height: 150px;"></div>', unsafe_allow_html=True)

    st.title("📰 News Intelligence Dashboard")
    st.caption(f"対象: **{keyword}** | 期間: {date_range[0]} 〜 {date_range[1]}")

    if start_button:
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            with st.status("🔍 データを収集中...", expanded=True) as status:
                st.write("Google News RSSから情報を抽出中...")
                
                search_query = keyword.replace("　", " ").replace(" ", "+")
                exclude_domain = "city.kitakyushu.lg.jp"
                query = f"{search_query}+-site:{exclude_domain}+-site:instagram.com"
                
                date_query = f"after:{start_date}+before:{end_date + datetime.timedelta(days=1)}"
                url = f"https://news.google.com/rss/search?q={query}+{date_query}&hl=ja&gl=JP&ceid=JP:ja&num={max_results}"
                feed = feedparser.parse(url)
                
                st.write("高純度フィルタリングを実行中...")
                articles = []
                all_text_for_analysis = ""

                target_words = keyword.replace("　", " ").split()

                for entry in feed.entries[:max_results]:
                    if all(word.lower() in entry.title.lower() for word in target_words):
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            dt = datetime.datetime(*entry.published_parsed[:6])
                            entry_date = dt.date()
                            
                            if start_date <= entry_date <= end_date:
                                summary = entry.summary if hasattr(entry, 'summary') else ""
                                clean_summary = re.sub(r'<[^>]+>', '', summary)
                                all_text_for_analysis += entry.title + " " + clean_summary + " "
                                
                                articles.append({
                                    "日付": entry_date,
                                    "メディア": entry.source.title if hasattr(entry, 'source') else "不明",
                                    "タイトル": entry.title,
                                    "リンク": entry.link
                                })
                                
                status.update(label="✅ 分析完了", state="complete", expanded=False)

            if articles:
                df = pd.DataFrame(articles).sort_values("日付", ascending=False)
                df.insert(0, 'No', range(1, len(df) + 1))
                
                stop_words = [
                    "の", "に", "は", "た", "を", "で", "と", "が", "も", "な", "し", "て", "した", "ある", "いう", "から", "など", "ニュース", "記事",
                    "yahoo", "ヤフー", "西日本新聞", "me", "ポータル", "web", "配信", "発表", "掲載", "提供", "公式", "サイト",
                    "編集", "部", "毎日新聞", "読売新聞", "朝日新聞", "産経新聞", "時事通信", "共同通信", "日本経済新聞", "日経","nbsp","西日本新聞me","co","jp","Webポータル","au","メニューニュース","速報","nnn","news",
                    "article","TBS","FNN","FNNプライムオンライン","九州朝日放送","KBC","FBS福岡放送","RKB毎日放送","TNCテレビ西日本","dig","日テレnews","福岡",
                    "instagram", "インスタ", "インスタグラム", "投稿", "フォロワー", "反響", "話題","nishinippon",
                ]
                stop_words.extend([w.lower() for w in target_words])

                clean_text = all_text_for_analysis.lower()
                sorted_stops = sorted(list(set(stop_words)), key=len, reverse=True)
                for sw in sorted_stops:
                    clean_text = clean_text.replace(sw.lower(), " ")

                words = re.findall(r'[一-龥ぁ-んァ-ヶーa-zA-Z0-9]+', clean_text)
                filtered_words = [w for w in words if len(w) >= 2 and not w.isdigit()]
                
                top_word = "N/A"
                if filtered_words:
                    word_counts = pd.Series(filtered_words).value_counts().reset_index()
                    word_counts.columns = ["単語", "出現数"]
                    top_word = word_counts.iloc[0]["単語"]

                m1, m2, m3 = st.columns(3)
                m1.metric("総記事数", f"{len(df)} 件")
                m2.metric("最多掲載メディア", df["メディア"].value_counts().idxmax())
                m3.metric("最頻出ワード", top_word)
                st.divider()
                
                tab1, tab2, tab3, tab4 = st.tabs(["📈 掲載トレンド", "🏢 メディアシェア", "🔍 キーワード分析", "📑 詳細データ"])
                with tab1:
                    st.subheader("日別掲載数の推移")
                    daily_counts = df.groupby("日付").size().reset_index(name="記事数")
                    st.line_chart(data=daily_counts, x="日付", y="記事数")
                with tab2:
                    st.subheader("主要掲載メディア（上位10）")
                    media_counts = df["メディア"].value_counts().reset_index()
                    media_counts.columns = ["メディア", "記事数"]
                    st.bar_chart(data=media_counts.head(10), x="メディア", y="記事数")
                with tab3:
                    st.subheader("頻出単語ランキング")
                    if filtered_words:
                        st.bar_chart(data=word_counts.head(15), x="単語", y="出現数")
                with tab4:
                    st.subheader("詳細データ一覧")
                    st.data_editor(df, column_config={"No": st.column_config.NumberColumn("No", width="small"), "リンク": st.column_config.LinkColumn("リンク", display_text="記事へ")}, hide_index=True, use_container_width=True)
                    csv = df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 CSVダウンロード", data=csv, file_name=f"Report_{keyword}.csv", mime="text/csv")
            else:
                st.warning("指定した期間・キーワードに一致するニュースが見つかりませんでした。")
        else:
            st.warning("分析期間を正しく選択してください。")
