# HALAMAN APLIKASI SJB


def upload_page(*, aggregate_product_data, build_clustering_report_html, card_container, get_active_selected_data, get_cluster_order, load_uploaded_file, preprocess_data, reset_analysis_results, reset_date_filter_state, run_clustering, save_dataset_history, section_header, st, top_bar):
    top_bar("Clustering", "Upload, validasi dataset, dan jalankan clustering dengan mudah.")

    if st.session_state.role not in ["owner", "admin"]:
        st.error("Fitur ini hanya dapat diakses oleh Owner atau Admin.")
        return

    with card_container():
        section_header("Upload & Validasi Dataset", "Fitur yang digunakan: Quantity, Order, dan Omzet")
        uploaded_file = st.file_uploader("Pilih file data penjualan", type=["csv", "xlsx"], key="combined_upload_file")
        make_active = st.toggle("Gunakan dataset ini sebagai Dataset Aktif di Dashboard", value=True)
        process_upload = st.button("Upload & Validasi Dataset", disabled=uploaded_file is None)

            #Extract
            # Tahap Extract mengambil data dari file CSV atau Excel.
        if process_upload and uploaded_file is not None:
            df_raw = load_uploaded_file(uploaded_file)
            if df_raw is not None:
                df_selected = preprocess_data(df_raw)
                if df_selected is not None and not df_selected.empty:
                    # lOAD : disimpan ke tabel datasets di SQLite.
                    dataset_id = save_dataset_history(df_selected, uploaded_file.name, st.session_state.username, make_active=make_active)
                    st.session_state.analysis_dataset_id = dataset_id
                    st.session_state.analysis_dataset_name = uploaded_file.name
                    st.session_state.analysis_df_selected = df_selected.copy()
                    reset_analysis_results()
                    
                    if make_active:
                        st.session_state.active_dataset_id = dataset_id
                        st.session_state.df_selected = df_selected.copy()
                        st.session_state.df_product = aggregate_product_data(df_selected)
                        reset_date_filter_state()
                    st.success("✓ Dataset berhasil divalidasi dan disimpan.")
                else:
                    st.error("Gagal memproses data.")

    analysis_df = st.session_state.get("analysis_df_selected")
    analysis_dataset_name = st.session_state.get("analysis_dataset_name")

    if analysis_df is None or analysis_df.empty:
        analysis_df, analysis_dataset_name = get_active_selected_data()

    if analysis_df is not None and not analysis_df.empty:
        df_product = aggregate_product_data(analysis_df)
        with card_container():
            section_header("Jalankan Clustering", f"Dataset saat ini: {analysis_dataset_name}")
            
            # Pilihan Nilai K interaktif sebelum menjalankan clustering
            selected_k = st.slider("Tentukan Jumlah Cluster (K)", min_value=2, max_value=6, value=3, step=1, key="input_k_slider")
            
            if st.button("Jalankan Clustering"):
                if run_clustering(df_product, selected_k, dataset_id=st.session_state.get("analysis_dataset_id"), dataset_name=analysis_dataset_name, save_history=True):
                    st.success("✓ Clustering berhasil")

        result = st.session_state.get("clustering_result")
        if result is not None:
            with card_container():
                section_header("Ringkasan Hasil Clustering", "Hasil segmentasi produk")
                df_res = result["df_result"]
                
                counts = df_res["Kategori_Cluster"].value_counts()
                st.caption(f"Jumlah cluster (K): {result['k']}. Kategori diurutkan berdasarkan performa relatif Quantity, Order, dan Omzet.")
                for category in get_cluster_order(result["k"]):
                    if category in counts.index:
                        st.markdown(f"- **{category}**: {int(counts[category])} produk")

                col_down, col_exp, col_spacer = st.columns([1, 1, 5.8])
                with col_down:
                    report_html = build_clustering_report_html(result, analysis_dataset_name)
                    st.download_button(
                        "Export Laporan",
                        data=report_html.encode("utf-8"),
                        file_name="clustering_report.html",
                        mime="text/html"
                    )
                with col_exp:
                    st.download_button(
                    "Download CSV",
                        data=df_res.to_csv(index=False).encode("utf-8"),
                        file_name="hasil_clustering_penjualan.csv",
                        mime="text/csv"
                    )


def insight_page(*, format_number, format_rupiah, get_cluster_order, get_valid_clustering_result, safe_html, st, top_bar):
    top_bar("Insight & Recommendation", "Interpretasi bisnis dan tindakan yang disarankan untuk setiap cluster.")

    result = get_valid_clustering_result()
    if result is None:
        st.warning("Belum ada hasil clustering yang valid. Jalankan K-Means melalui halaman Clustering.")
        return

    df_result = result["df_result"]
    preferred_order = get_cluster_order(result["k"])
    available_categories = list(df_result["Kategori_Cluster"].dropna().unique())
    ordered_categories = [cat for cat in preferred_order if cat in available_categories] + [cat for cat in available_categories if cat not in preferred_order]

    if not ordered_categories:
        st.info("Kategori cluster belum tersedia.")
        return

    cluster_columns = st.columns(min(3, len(ordered_categories)))

    for index, category in enumerate(ordered_categories):
        cluster_df = df_result[df_result["Kategori_Cluster"] == category].copy()
        top_product = cluster_df.sort_values("Revenue", ascending=False).iloc[0]
        recommendation = (cluster_df["Rekomendasi"].dropna().astype(str).iloc[0] if cluster_df["Rekomendasi"].notna().any() else "Lakukan analisis lanjutan terhadap kelompok produk ini.")

        if category in ["Cluster Sangat Tinggi", "Cluster Tinggi"]: accent_class = "cluster-high"
        elif category in ["Cluster Menengah Atas", "Cluster Sedang", "Cluster Menengah Bawah"]: accent_class = "cluster-medium"
        elif category in ["Cluster Rendah", "Cluster Sangat Rendah"]: accent_class = "cluster-low"
        else: accent_class = "cluster-default"

        insight_text = f"{len(cluster_df)} produk menghasilkan {format_number(cluster_df['Quantity'].sum())} unit dan {format_rupiah(cluster_df['Revenue'].sum())}. Produk utama: {top_product['Product Name']}."

        with cluster_columns[index % len(cluster_columns)]:
            st.markdown(f"""
            <div class="cluster-insight-card {accent_class}">
                <div class="cluster-insight-title">{safe_html(category)}</div>
                <div class="cluster-insight-label">Insight</div>
                <div class="cluster-insight-text">{safe_html(insight_text)}</div>
                <div class="cluster-insight-label">Recommendation</div>
                <div class="cluster-insight-text">{safe_html(recommendation)}</div>
            </div>
            """, unsafe_allow_html=True)


def dataset_history_page(*, activate_dataset, card_container, clear_sales_data_db, delete_dataset_history, get_active_dataset_record, get_connection, get_dataset_history, interactive_table, load_dataset_by_id, reset_analysis_results, reset_date_filter_state, section_header, st, top_bar, use_dataset_for_analysis):
    top_bar("Riwayat Dataset", "Lihat, aktifkan, unduh, dan kelola dataset yang pernah diunggah.")
    history_df = get_dataset_history()

    with card_container():
        section_header("Dataset Aktif", "Dashboard selalu membaca dataset yang berstatus aktif.")
        active_record = get_active_dataset_record()
        if active_record is None: st.info("Dataset aktif: Data Default k-means.xlsx")
        else: st.success(f"Dataset aktif: {active_record['name']}")

        if st.button("Gunakan Data Default k-means.xlsx", key="use_default_dataset"):
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE datasets SET is_active=0")
                conn.commit()

            except Exception:
                conn.rollback()
                raise

            finally:
                cursor.close()
                conn.close()
            clear_sales_data_db()
            st.session_state.active_dataset_id = None
            st.session_state.df_selected = None
            st.session_state.df_product = None
            st.session_state.analysis_dataset_id = None
            st.session_state.analysis_dataset_name = None
            st.session_state.analysis_df_selected = None
            reset_analysis_results()
            reset_date_filter_state()
            st.success("Dashboard kembali menggunakan Data Default k-means.xlsx.")
            st.rerun()

    if history_df.empty:
        st.info("Belum ada riwayat dataset upload.")
        return

    display_df = history_df.copy()
    display_df["Status"] = display_df["is_active"].map({1: "Aktif", 0: "Tidak Aktif"})
    display_df = display_df.rename(columns={"id": "ID", "name": "Nama Dataset", "uploaded_at": "Tanggal Upload", "uploaded_by": "Pengguna"})

    with card_container():
        section_header("Daftar Dataset", "Seluruh upload tersimpan dan dapat dipakai kembali.")
        interactive_table(display_df[["ID", "Nama Dataset", "Tanggal Upload", "Pengguna", "Status"]], key="dataset_history_table", page_size=10, default_sort="Tanggal Upload")

    dataset_options = {f"#{row.id} - {row.name} ({row.uploaded_at})": row.id for row in history_df.itertuples(index=False)}
    selected_label = st.selectbox("Pilih Dataset", list(dataset_options.keys()), key="dataset_history_select")
    selected_id = dataset_options[selected_label]
    record = load_dataset_by_id(selected_id)

    if record is None:
        st.error("Dataset tidak ditemukan.")
        return

    with card_container():
        section_header("Detail Dataset", record["name"])
        interactive_table(record["data"].rename(columns={"Revenue": "Omzet"}), key=f"dataset_detail_{selected_id}", page_size=10)

        col_analysis, col_activate, col_download, col_delete, col_spacer = st.columns([1.4, 1.4, 1.3, 1.6, 4], gap=None)
        with col_analysis:
            if st.button("Analisis Dataset", key=f"analyze_dataset_{selected_id}"):
                if use_dataset_for_analysis(selected_id): st.success("Dataset dipilih untuk analisis tanpa mengubah Dataset Aktif Dashboard.")
        with col_activate:
            if st.button("Aktifkan Dataset", key=f"activate_dataset_{selected_id}"):
                if activate_dataset(selected_id):
                    st.success("Dataset berhasil dijadikan Dataset Aktif Dashboard.")
                    st.rerun()
        with col_download:
            st.download_button("Download CSV", data=record["data"].to_csv(index=False).encode("utf-8"), file_name=f"dataset_{selected_id}.csv", mime="text/csv", key=f"download_dataset_{selected_id}")
        with col_delete:
            if st.session_state.role == "owner":
                confirm_delete = st.checkbox("Konfirmasi hapus", key=f"confirm_delete_dataset_{selected_id}")
                if st.button("Hapus Dataset", key=f"delete_dataset_{selected_id}", disabled=not confirm_delete):
                    if delete_dataset_history(selected_id):
                        st.success("Dataset berhasil dihapus.")
                        st.rerun()


def clustering_history_page(*, card_container, delete_clustering_history, get_clustering_history, interactive_table, load_clustering_history_by_id, section_header, st, top_bar):
    top_bar("Riwayat Hasil Clustering", "Buka, download, dan kelola hasil clustering terdahulu.")
    history_df = get_clustering_history()

    if history_df.empty:
        st.info("Belum ada riwayat hasil clustering.")
        return

    display_df = history_df.rename(columns={"id": "ID", "clustered_at": "Tanggal Clustering", "dataset_name": "Dataset", "clustered_by": "Pengguna", "k": "Nilai K", "silhouette": "Silhouette Score", "dbi": "Davies-Bouldin Index"})
    with card_container():
        section_header("Daftar Riwayat", "Daftar hasil proses clustering yang telah disimpan.")
        interactive_table(display_df[["ID", "Tanggal Clustering", "Dataset", "Pengguna", "Nilai K", "Silhouette Score", "Davies-Bouldin Index"]], key="clustering_history_table", page_size=10, default_sort="Tanggal Clustering")

    history_options = {f"#{row.id} - {row.dataset_name} | k={row.k} | {row.clustered_at}": row.id for row in history_df.itertuples(index=False)}
    selected_label = st.selectbox("Pilih data yang ingin dilihat", ["Pilih data"] + list(history_options.keys()), key="clustering_history_select")

    if selected_label == "Pilih data": return
    record = load_clustering_history_by_id(history_options[selected_label])

    if record is None:
        st.warning("Data riwayat tidak ditemukan.")
        return

    with card_container():
        section_header(f"Hasil Clustering #{record['id']}", f"{record['dataset_name']} - {record['clustered_at']}")
        interactive_table(record["df_result"].rename(columns={"Revenue": "Omzet", "Revenue_Per_Transaksi": "Omzet per Transaksi"}), key=f"clustering_history_detail_{record['id']}", page_size=10, default_sort="Omzet")
        col_download, col_action, col_space = st.columns([1.3, 2.0, 3.2], gap="small")
        with col_download:
            st.download_button("Download Hasil CSV", data=record["df_result"].to_csv(index=False).encode("utf-8"), file_name=f"hasil_clustering_{record['id']}.csv", mime="text/csv", key=f"download_history_{record['id']}")
        with col_action:
            if st.session_state.role == "owner":
                confirm_key = f"confirm_delete_history_{record['id']}"
                col_confirm, col_delete = st.columns([1.2, 1], gap="small")
                with col_confirm: confirm_delete = st.checkbox("Konfirmasi hapus", key=confirm_key)
                with col_delete:
                    if st.button("Hapus Riwayat", key=f"delete_history_{record['id']}", disabled=not confirm_delete):
                        if delete_clustering_history(record["id"]):
                            st.success("Riwayat clustering berhasil dihapus.")
                            st.rerun()


def user_management_page(*, add_user, card_container, delete_user, get_all_users, section_header, show_table, st, top_bar):
    top_bar("Manajemen User", "Owner dapat menambahkan akun admin baru dan menghapus pengguna.")

    if st.session_state.role != "owner":
        st.error("Halaman ini hanya dapat diakses oleh owner.")
        return

    with card_container():
        section_header("Tambah User Admin", "Owner dapat menambahkan akun baru dengan role admin.")
        with st.form("add_admin_form"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Simpan")
            if submit:
                if new_username.strip() == "" or new_password.strip() == "": st.error("Username dan password tidak boleh kosong.")
                else:
                    success = add_user(new_username, new_password, "admin")
                    if success: st.success("User admin berhasil ditambahkan.")
                    else: st.error("Username sudah digunakan.")

    with card_container():
        section_header("Daftar User", "Daftar pengguna yang tersimpan dalam database.")
        df_users = get_all_users()
        show_table(df_users)
        
        st.markdown("### Hapus User")
        user_options = {f"{row.username} ({row.role})": row.id for row in df_users.itertuples(index=False)}
        selected_user = st.selectbox("Pilih pengguna yang akan dihapus", list(user_options.keys()))
        
        if st.button("Hapus Pengguna"):
            if delete_user(user_options[selected_user]):
                st.success(f"Pengguna {selected_user} berhasil dihapus.")
                st.rerun()
            else:
                st.error("Gagal menghapus pengguna.")
