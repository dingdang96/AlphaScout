# AlphaScout - Web3 项目与 X 动态自动化监控系统

AlphaScout 是一个专为 Web3 Alpha 玩家设计的自动化数据采集、筛选与告警守护程序。

## 核心功能
1. **RootData 抓取**：自动提取最新上线与最新融资的 Web3 项目，包含官网、X、Discord 与发币状态。
2. **未发币过滤**：仅监控 `has_token == False` 的未发币项目，降低风控与无效噪音。
3. **Alpha Pattern 打分**：通过 VC 背景、融资额与 LLM 对比，筛选社区友好、反 PUA 项目并开启优先轮询。
4. **X 增量监控**：轮询增量推文，具备阶梯延时防封号能力。
5. **多端推送**：支持 Telegram 与飞书富文本交互卡片推送。

## 快速启动

1. **环境准备**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境变量**
   复制 `.env.example` 为 `.env` 并填写对应配置：
   ```bash
   cp .env.example .env
   vim .env
   ```

3. **赋予脚本执行权限并启动后台服务**
   ```bash
   chmod +x *.sh
   ./start.sh
   ```

4. **查看运行状态**
   ```bash
   ./status.sh
   ```