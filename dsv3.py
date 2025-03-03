import streamlit as st
import requests
import json
from datetime import datetime
from openai import OpenAI  # 新增导入

# 页面配置
st.set_page_config(
    page_title="词汇结构分析 Based on DeepSeek",
    page_icon="📊",
    layout="centered"
)

# 初始化session状态
if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""
if "last_api_key" not in st.session_state:  # 新增：存储上一次的API密钥
    st.session_state.last_api_key = "sk-79f1099de3dc46a7b4650ae698c26d97"

def split_content(content, max_words=300):
    """将内容按最大词数分割"""
    words = content.split()
    chunks = [' '.join(words[i:i + max_words]) for i in range(0, len(words), max_words)]
    return chunks

def deepseek_inference(api_key="sk-79f1099de3dc46a7b4650ae698c26d97", prompt='', temperature=0.7, max_tokens=8192):
    """
    调用DeepSeek-V3 API进行推理
    """
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True  # 启用流式响应
        )
        
        # 流式处理响应
        result = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                result += content
                yield content  # 实时返回生成的内容
        return result
    except Exception as e:
        st.error(f"API请求失败: {str(e)}")
        return None

def save_to_file(content):
    """生成下载文件"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"deepseek_output_{timestamp}.txt"
    return filename, content

# 页面标题
st.title("词汇结构分析 Based on DeepSeek-V3")

st.markdown("""By 北京大学吴云芳NLP组""")

st.markdown("""---""")

# 修改侧边栏设置
with st.sidebar:
    st.header("⚙️ 设置")
    api_key = st.text_input("API密钥", 
                          type="password", 
                          placeholder="请输入您的DeepSeek API密钥",
                          value=st.session_state.last_api_key,  # 使用上一次输入的值
                          help="已提供默认API密钥，如有需要请输入您的DeepSeek API密钥")
    st.session_state.last_api_key = api_key  # 保存当前输入的API密钥
    temperature = 0.7
    with st.expander("📖 使用说明", expanded=True):
        st.markdown("""
        1. 在侧边栏输入您的有效的API密钥，申请方法见 [DeepSeek API Keys](https://platform.deepseek.com/api_keys)
        3. 在文本框中输入清晰的词汇列表，或上传txt文件
        4. 点击「生成文本」按钮开始生成
        5. 生成完成后可下载结果文件
        
        **注意事项：**
        - 请妥善保管您的API密钥
        - 生成结果不能保证准确性，请谨慎使用
        """)
    # temperature = st.slider("创意度", 0.0, 2.0, 0.7, step=0.1, 
    #                       help="值越大生成内容越随机，值越小越确定")
    # max_tokens = st.number_input("最大长度", 100, 2000, 500, step=50,
    #                            help="控制生成内容的最大长度")

# 主界面
prompt = "你是一个汉语语法研究者，现在我会给你一些繁体或简体的汉语词汇，请你帮我将每一个词归类成单纯词、主谓型复合合成词、述宾型复合合成词、述补型复合合成词、偏正型复合合成词、联合型复合合成词、附加式合成词、重叠式合成词这8个类别中的一个类别，其中:\n1. 单纯词：由一个语素构成的词叫做单纯词。\n2. 主谓型复合合成词：前一词根表示被陈述的事物，后一词根是陈述前一词根的，这样的复合式合成词叫主谓型复合合成词。\n3. 述宾型复合合成词：前一个词根表示动作、行为，后一个词根表示动作、行为所支配关涉的事物，这样的复合式合成词叫述宾复合合成词。\n4. 述补型复合合成词：后一个词根补充说明前一个词根的复合式合成词。\n5. 偏正型复合合成词：前一个词根修饰、限制后一个词根的复合式合成词。\n6. 联合型复合合成词：由两个意义相同、相近、相关或相反的词根并列组合而成的复合式合成词。\n7. 附加式合成词：由词根和词缀构成的合成词。\n8. 重叠式合成词：由相同的词根语素重叠构成的合成词。\n请输出每一个词对应的分类结果，并在最后输出每一种类别的统计个数。"

uploaded_file = st.file_uploader("上传词汇文件 (.txt)", type=["txt"])
if uploaded_file is not None:
    content = uploaded_file.read().decode("utf-8")
else:
    content = st.text_area("输入词汇条目", height=150, placeholder="请输入您需要分析的词汇，每个条目一行，建议不超过300个词...")

# user_content = content  # 将用户输入的内容单独保存

temperature = 0.3
max_tokens = 8192
# 生成按钮
# col1, col2 = st.columns([1, 3])
# with col1:
generate_btn = st.button("🚀 生成文本", use_container_width=True)

# 处理生成请求
if generate_btn:
    if not content:
        st.warning("⚠️ 请输入内容")
        st.stop()

    # 分割内容
    content_chunks = split_content(content)
    if len(content_chunks) > 1:
        st.info(f"检测到词汇数量超过300个，将分成{len(content_chunks)}次生成")

    with st.spinner("正在生成，请稍候..."):
        all_results = []
        st.markdown("""---""")
        st.markdown("### 生成结果")
        for i, chunk in enumerate(content_chunks):
            if len(content_chunks) > 1:
                st.write(f"正在处理第 {i+1}/{len(content_chunks)} 部分...")
            
            # 创建输出容器
            output_container = st.empty()
            chunk_result = ""
            
            # 将基础prompt与当前分块内容组合
            chunk_prompt = prompt + "\n词汇列表：\n" + chunk
            for content in deepseek_inference(api_key, chunk_prompt, temperature, max_tokens):
                chunk_result += content
                output_container.markdown(chunk_result)  # 实时更新显示内容
            
            if chunk_result:
                all_results.append(chunk_result)
            else:
                st.error(f"第 {i+1} 部分生成失败")
                break

    if all_results:
        final_result = "\n\n".join(all_results)
        st.session_state.generated_text = final_result
        st.success("生成完成！")
        # st.write(final_result)
        
        filename, content = save_to_file(st.session_state.generated_text)
        st.download_button(label="💾 下载结果", 
                          data=final_result,
                          file_name=filename,
                          mime="text/plain",
                          use_container_width=True)
    else:
        st.error("文本生成失败，请检查设置后重试")
        
st.markdown("""---""")
# 使用说明
st.markdown("""
**开发者声明：**
本工具由北京大学吴云芳老师组开发，基于DeepSeek-V3 API实现。工具旨在为汉语语法研究提供辅助分析功能，还在持续优化中，生成结果仅供参考，请结合专业知识进行判断。如有任何问题或建议，欢迎通过邮件联系开发者。

**免责声明：**
本工具生成的结果基于人工智能模型，可能存在误差或不确定性。开发者不对使用本工具产生的任何直接或间接后果负责。用户应自行判断结果的准确性，并承担使用风险。

**联系方式：**
caiyida@stu.pku.edu.cn
""")