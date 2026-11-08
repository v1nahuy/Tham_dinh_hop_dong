import streamlit as st

st.set_page_config(page_title="Thẩm định hợp đồng", layout="wide")

navigation = st.navigation(
    [
        st.Page("ui/so_hoa.py", title="Số hóa", icon="📄", default=True),
        st.Page("ui/tham_dinh.py", title="Thẩm định", icon="⚖️"),
        st.Page("ui/ket_qua.py", title="Kết quả", icon="📋"),
    ]
)
navigation.run()
