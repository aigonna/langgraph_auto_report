# LangGraph Tools - 多分支数据分析系统

基于LiteLLM的多模型数据分析框架，支持多种大模型API。

## 环境配置

### 1. 安装依赖
```bash
pip install litellm langchain-community pandas matplotlib seaborn numpy
```

### 2. 环境变量配置

创建 `.env` 文件，根据你使用的模型配置相应的API密钥：

#### 使用GPT-4o (推荐)
```bash
# 模型配置
MODEL_NAME=gpt-4o
TEMPERATURE=0.1
MAX_TOKENS=4000

# OpenAI API (支持第三方代理)
OPENAI_API_KEY=your_openai_api_key
# 如果使用第三方API，设置base_url
OPENAI_BASE_URL=https://your-proxy-url.com/v1
# 或者使用其他变量名
openai_key=your_openai_api_key
openai_base_url=https://your-proxy-url.com/v1
```

#### 使用DeepSeek
```bash
MODEL_NAME=deepseek/deepseek-chat
deepseek=your_deepseek_api_key
```

#### 使用其他模型
```bash
# Claude
MODEL_NAME=claude-3-sonnet-20240229
ANTHROPIC_API_KEY=your_anthropic_key

# Gemini
MODEL_NAME=gemini/gemini-pro
GOOGLE_API_KEY=your_google_key

# 通义千问
MODEL_NAME=qwen/qwen-turbo
DASHSCOPE_API_KEY=your_dashscope_key

# GLM
MODEL_NAME=zhipuai/glm-4
ZHIPUAI_API_KEY=your_zhipuai_key
```

## 支持的模型

### OpenAI系列
- `gpt-4o` (推荐)
- `gpt-4-turbo`
- `gpt-3.5-turbo`

### 国产模型
- `deepseek/deepseek-chat`
- `qwen/qwen-turbo`
- `zhipuai/glm-4`

### 其他模型
- `claude-3-sonnet-20240229`
- `gemini/gemini-pro`

## 功能特性

### 🔧 专业工具集 (16个工具)
1. **数据读取**: `read_csv_data` - 智能编码检测
2. **统计分析**: `data_statistics_analysis` - 全面统计分析
3. **可视化**: `create_visualization` - 7种图表类型
4. **趋势分析**: `trend_analysis` - 时间序列分析
5. **分类分析**: `category_analysis` - 排名和占比分析
6. **相关性**: `correlation_analysis` - 变量关系分析
7. **异常检测**: `outlier_detection` - 异常值识别
8. **数据导出**: `data_export` - 多格式导出
9. **文件操作**: `create_file`, `read_file_content`, `list_files`
10. **基础工具**: `shell_exec`, `str_replace`

### 📊 多分支分析架构
- **8-12个分析分支**：时间、分类、地理、绩效、关系、异常、细分、预测
- **每分支2-3个图表**：总共15-20+个专业可视化
- **详细分支总结**：每分支500+字深度分析
- **跨分支整合**：综合洞察和战略建议

### 📈 分析深度
- **2000+字综合报告**
- **量化洞察**：具体数值、百分比、排名
- **商业建议**：可执行的战略建议
- **多维度视角**：全方位数据分析

## 使用方法

1. **配置环境变量**
2. **准备数据文件** (放在 `./data/` 目录)
3. **运行分析**:
```bash
python graphs.py
```

## 输出结果

系统会在 `output/YYYYMMDD_HHMMSS_task_description_uuid/` 目录下生成：

- **分支分析文件**: `branch_[name]_*.md`, `branch_[name]_*.png`
- **统计结果**: `*_analysis_results.json`
- **可视化图表**: `*.png` (15-20个图表)
- **综合报告**: `comprehensive_multi_branch_report.md`

## 故障排除

1. **模型切换**: 修改 `MODEL_NAME` 环境变量
2. **API配置**: 检查对应模型的API密钥配置
3. **网络问题**: 配置 `OPENAI_BASE_URL` 使用代理
4. **依赖问题**: 确保安装了所有必要的包

## 推荐配置

**最佳性能**: GPT-4o + 第三方API代理
**成本优化**: DeepSeek Chat
**备用方案**: GPT-3.5-turbo 