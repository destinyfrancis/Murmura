export default {
  nav: {
    home: '首頁',
    workspace: '工作區',
    learn: '教學',
    about: '關於',
    report: '報告生成',
    godView: '上帝視角',
    settings: '設定',
  },
  godView: {
    header: {
      terminal: '上帝視角終端 (GOD VIEW)',
      selectSession: '-- 選擇模擬會話 --',
      loading: '載入中...',
      refresh: '重新整理',
      autoOn: '自動更新 開',
      autoOff: '自動更新 關',
      autoDelayed: '自動更新 (延遲)'
    },
    status: {
      signals: '市場訊號',
      active: '有效',
      buyYes: '買入 YES',
      buyNo: '買入 NO',
      hold: '觀望',
      contracts: '合約數量',
      lastRefreshed: '最後更新'
    },
    tabs: {
      main: '市場訊號',
      ensemble: '集成預測',
      scenarios: '情景比較',
      sentiment: '情緒熱圖'
    },
    panels: {
      contracts: {
        title: 'POLYMARKET 相關合約',
        loading: '正在獲取相關合約...',
        empty: '此會話沒有匹配的合約。'
      },
      signals: {
        title: '交易訊號',
        loading: '正在根據代理共識計算訊號...',
        empty: '尚未產生訊號。請確保模擬已完成至少 5 輪。'
      },
      consensus: {
        title: '代理共識',
        sentimentTrend: '情緒趨勢',
        signalBreakdown: '訊號詳情',
        recentDecisions: '最近決策',
        noData: '暫無數據',
        awaiting: '等待代理人決策中...'
      },
      feed: {
        title: '實時代理動態',
        empty: '尚未有代理活動。',
        posts: '則動態'
      }
    },
    placeholders: {
      selectSession: '請選擇一個模擬會話以開始',
      godViewDesc: '上帝視角終端顯示基於代理人共識的實時 Polymarket 交易訊號'
    }
  },
  interaction: {
    welcome: '歡迎進入深度交互模式。你可以針對報告內容提問，或者同個別代理人對話。',
    noResponse: '（無回應）',
    sendFailed: '發送失敗：',
    settings: {
      title: '對話設定',
      target: '對話對象',
      analyst: '報告分析師',
      agent: '指定代理人',
      selectAgent: '選擇代理人',
      selectPlaceholder: '請選擇...',
      whatIf: 'What-If 參數',
      whatIfHint: '喺對話中描述假設情景，例如「如果失業率升到 8%」'
    },
    chat: {
      you: '你',
      ai: 'AI',
      system: '系統',
      error: '錯誤',
      placeholder: '輸入你嘅問題...',
      sending: '發送中...',
      send: '發送'
    }
  },
  lessons: {
    overview: {
      traditional: {
        title: '傳統民調',
        points: [
          '詢問 1,000 人的看法',
          '靜態快照 — 一次性',
          '忽略社交影響力',
          '無法模擬政策變化'
        ],
        verdict: '有限'
      },
      murmura: {
        title: 'Murmura',
        points: [
          '模擬 500 個 AI 代理人互動',
          '動態演化 — 30+ 輪模擬',
          'Echo Chamber + 信任網絡',
          '即時注入政策衝擊'
        ],
        verdict: '湧現式預測'
      },
      text1: 'Murmura 不是詢問人們「你在想什麼」，而是利用 AI 代理人模擬真實的社會互動過程。每個代理人都有自己的性格、記憶、信任圈子，他們會互相影響，最終<strong>湧現</strong>出群體趨勢。',
      text2: '我們追蹤的指標包括：房價信心、移民意向、消費模式、政治極化度等。'
    },
    uncertainty: {
      intro: 'Murmura 的預測不確定性來自四個主要來源。點擊每個來源了解更多：',
      closing: '透明地呈現不確定性是負責任 AI 預測的核心原則。Murmura 不是「預言機」，而是幫助思考多個可能未來的工具。',
      sources: {
        behavior: { label: '代理人行為隨機性', detail: '每個 AI 代理人的 LLM 決策具有內在隨機性，無法完全控制。' },
        macro: { label: '宏觀數據誤差', detail: 'GDP、失業率等宏觀數據存在測量誤差與修訂，直接影響初始條件。' },
        model: { label: '模型結構假設', detail: '消費函數、信任衰減率等參數是由校準數據估計，具有統計不確定性。' },
        shocks: { label: '外部衝擊不可預測性', detail: '地緣政治事件、自然災害等外生衝擊無法提前納入模型。' }
      }
    },
    kg: {
      intro: '知識圖譜將複雜議題拆解成 <strong>實體</strong>（節點）與 <strong>關係</strong>（邊）。將滑鼠移到節點上方查看描述。',
      closing: '模擬過程中，代理人的行動會更新圖譜上的邊權重 — 反映因果關係強度的變化。',
      types: {
        economic: '經濟',
        person: '人物',
        policy: '政策',
        organization: '組織',
        social: '社會',
        location: '地點'
      },
      nodes: {
        hibor: 'HIBOR利率',
        mortgage: '按揭利率',
        prices: '樓價指數',
        buyers: '首置買家',
        tax: '印花稅',
        bank: '匯豐銀行',
        hardlife: '上車難',
        migration: '移民潮',
        shatin: '沙田',
        fed: '美聯儲'
      }
    },
    boids: {
      intro: '代理人行為遵循三條簡單規則，類似於鳥群飛行（Boids 理論）：',
      rules: {
        alignment: { title: '對齊性', desc: '與鄰居朝向相同方向（社會共識）。' },
        cohesion: { title: '凝聚力', desc: '向鄰居的平均位置靠攏（信任建立）。' },
        separation: { title: '分離性', desc: '避免與衝突實體過於接近（同溫層/回聲筒）。' }
      },
      closing: '沒有任何一隻鳥知道「群體隊伍」的概念 — 但隊形自然湧現。這就是 <strong>湧現 (Emergence)</strong>。',
      murmura: 'Murmura 同理 — 每個代理人只按自己的性格和記憶做決策，但整體會湧現出可預測的社會趨勢。'
    },
    ner: {
      intro: '每段種子文本都會經歷以下處理管道，最終成為知識圖譜中的節點與邊：',
      steps: ['原始文本', '分詞', 'NER 命名體識別', '關係抽取', 'KG 節點'],
      example: {
        label: '示例：',
        text: '「<strong>聯儲局</strong>宣布<strong>加息</strong> 0.25厘，影響<strong>香港樓市</strong>」',
        org: '聯儲局 (組織)',
        hike: '加息 (事件)',
        market: '香港樓市 (經濟)',
        announced: '宣布',
        affecting: '影響'
      },
      closing: '這個過程由 DeepSeek V3.2 驅動，自動識別實體類型與因果關係，構建結構化知識表示。'
    },
    shocks: {
      intro: '政策衝擊是 Murmura 系統的「壓力測試」。你可以在運行中的模擬中注入以下事件：',
      events: {
        interest_rate: { title: '加息衝擊', desc: '按揭利率突然上升 1%' },
        tax: { title: '撤銷印花稅', desc: '政府取消所有樓宇印花稅' },
        immigration: { title: '移民政策變動', desc: '推出全新計分制移民政策' }
      },
      text: '當注入衝擊時，代理人會重新評估他們的信念和信任網絡，導致整個系統產生「瀑布式」連鎖反應。'
    },
    percentiles: {
      intro: 'Murmura 不只輸出一條預測線，而是整個概率分佈。拖動滑桿調整情景強度：',
      chartLabel: '樓價信心指數預測',
      mild: '溫和衝擊',
      extreme: '極端衝擊',
      intensity: '情景強度',
      p10_90: 'p10–p90',
      p25_75: 'p25–p75',
      p50: 'p50 (中位數)',
      quiz: {
        q1: '問題 1：p50 代表什麼？',
        q1_opts: [
          { value: 'p50', label: '中位數預測' },
          { value: 'avg', label: '平均值' },
          { value: 'best', label: '最佳情景' }
        ],
        q1_correct: '正確！p50 即中位數，一半模擬結果高於此值，一半低於。',
        q1_wrong: '錯誤，p50 是中位數（第 50 百分位數），不是平均值。',
        q2: '問題 2：p10-p90 區間越寬代表什麼？',
        q2_opts: [
          { value: 'wide', label: '不確定性更高' },
          { value: 'certain', label: '預測更準確' },
          { value: 'same', label: '結果相同' }
        ],
        q2_correct: '正確！更寬的區間反映更高的預測不確定性。',
        q2_wrong: '錯誤，更寬的區間意味不確定性更高，不是更準確。'
      }
    },
    challenges: {
      intro: '模擬結果不應該被盲目接受。以下是 5 步批判性評估清單 — 每完成一步就剔一個：',
      allChecked: '全部完成！你已經掌握了批判性評估模型的方法。',
      reset: '重置',
      closing: '養成這 5 步習慣，可以幫助你避免過度依賴模型輸出，做出更明智的判斷。',
      assumptions: { label: '檢查假設', detail: '模型的初始假設是否合理？' },
      history: { label: '對比歷史', detail: '過去類似情境的結果如何？' },
      boundary: { label: '邊界測試', detail: '極端參數會產生什麼結果？' },
      counterfactual: { label: '反事實推理', detail: '如果某個因素不存在，結果會如何變化？' },
      omission: { label: '尋找遺漏', detail: '是否有重要因素被忽略？' }
    },
    mistakes: {
      intro: '在解讀 Murmura 模擬時，請避免以下常見誤區：',
      list: [
        { wrong: '模型顯示 70% 機率會下跌，所以一定會下跌', correct: '70% 機率代表 10 次中大約有 7 次會發生' },
        { wrong: 'p50 預測是最準確的', correct: 'p50 是中位數，真實結果可能在 p10-p90 之間' },
        { wrong: '代理人數量越多越準確', correct: '代理人的多樣性比數量更重要' },
        { wrong: '模型預測了黑天鵝事件', correct: '模型只能捕捉已知風險，真正的黑天鵝無法預測' },
        { wrong: '兩次模擬結果不同代表模型不可靠', correct: '隨機性是模型的特徵，而非缺陷' }
      ]
    },
    dataSources: {
      intro: 'Murmura 結合了高頻市場數據與低頻統計指標，以此奠定模擬的基礎：',
      category: '類別',
      items: '關鍵項目',
      frequency: '更新頻率',
      lag: '數據延遲',
      gov: { category: '政府統計', items: ['人口普查', '就業數據', '零售銷售'], frequency: '每月更新', lag: '約 2 個月' },
      finance: { category: '金融市場', items: ['恒生指數 (HSI)', '板塊指數', '成交量'], frequency: '實時', lag: '< 15 分鐘' },
      rates: { category: '利率數據', items: ['HIBOR', '聯儲局基準利率', 'USD/HKD'], frequency: '每日', lag: '1 個工作日' },
      social: { category: '社交媒體', items: ['RTHK 新聞', '論壇帖文', '輿情分析'], frequency: '每小時', lag: '< 1 小時' },
      macro: { category: '宏觀經濟', items: ['中國 GDP', 'CPI', '出口數據'], frequency: '每季', lag: '約 3 個月' }
    },
    meta: {
      t0: '系統預測什麼？',
      t1: '什麼是湧現？',
      t2: '知識圖譜入門',
      t3: '從證據到結構',
      t4: '從情景到結果',
      t5: '解讀概率預測',
      t6: '信心與不確定性',
      t7: '如何挑戰模型',
      t8: '常見錯誤',
      t9: '數據來源與局限'
    }
  },
  learn: {
    eyebrow: 'Operator Manual',
    title: '由種子文本到可追溯預測',
    subtitle: '這裡不是產品廣告，而是操作手冊：你會學識 Murmura 如何讀入情景、建構知識圖譜、生成代理人、運行 OASIS 模擬、解讀概率報告，以及如何質疑模型輸出。',
    metricsLabel: '教學摘要',
    indexLabel: '教學目錄',
    glossaryLabel: 'Quick Reference',
    glossaryTitle: '讀結果前先掌握的詞彙',
    metrics: [
      { value: '10', label: '教學章節' },
      { value: '05', label: '工作流步驟' },
      { value: '18', label: 'XAI 工具' },
      { value: 'p10-p90', label: '不確定區間' }
    ],
    workflow: [
      { label: 'Graph', desc: '把原始文本拆成實體、關係、隱含持份者與初始指標。' },
      { label: 'Env', desc: '把圖譜轉成代理人、平台身份、決策空間與場景配置。' },
      { label: 'Sim', desc: '逐輪運行代理人決策、信念更新、派系形成與宏觀回饋。' },
      { label: 'Report', desc: '用可解釋工具抽查證據、生成報告、輸出 PDF 或分享連結。' },
      { label: 'Interact', desc: '訪談代理人、追問假設、注入 shock、比較分支時間線。' }
    ],
    blocks: {
      whatHappens: '系統實際做什麼',
      howToRead: '你應該怎樣判讀',
      operatorRule: '操作守則'
    },
    modules: {
      overview: {
        code: 'START',
        title: 'Murmura 預測的是集體反應，不是單一答案',
        summary: '輸入一段 seed text 後，Murmura 會把它轉成一個可運行的社會、公司、市場或敘事世界。核心不是問 LLM「答案係咩」，而是讓不同代理人在同一個世界入面互相影響。',
        steps: [
          '讀取文本，保留你提供的時間線與語境。',
          '抽取明示角色、事件、地點、組織、資源與衝突。',
          '推斷未被明說但會受影響的持份者。',
          '讓代理人逐輪行動，觀察群體趨勢如何湧現。'
        ],
        checks: [
          '把輸出當成「多個可能未來的地圖」，不是預言。',
          '先看代理人、指標與 shock 是否符合原始文本。',
          '用報告證據與反事實分支檢查結果是否穩健。',
          '如果 seed text 偏窄，模擬世界亦會偏窄。'
        ],
        outcome: '好的使用方法是先定義問題，再讓系統構建世界；不要只貼一個標題就期待完整因果宇宙。'
      },
      workflow: {
        code: 'FLOW',
        title: '五步工作流如何連成一條預測流水線',
        summary: '每一步都會留下狀態：你可以停在圖譜檢查、重新生成環境、改 preset、重跑報告，或者在互動階段追問代理人。',
        steps: [
          'Step 1 建構 KG：抽取實體與關係，加入隱含持份者。',
          'Step 2 建立環境：生成代理人格、平台身份、初始記憶與決策空間。',
          'Step 3 運行模擬：OASIS 子程序按輪次輸出行動、信念與事件。',
          'Step 4 生成報告：ReACT 報告使用 XAI 工具引用數據與時間線。',
          'Step 5 深度互動：訪談代理人、追問證據、注入 what-if shock。'
        ],
        checks: [
          'Graph 錯，後面每一步都會被帶歪。',
          'Env 是代理人世界觀的入口，最值得抽樣檢查。',
          'Sim 要看趨勢、分歧與臨界點，不只看最後一輪。',
          'Report 是決策輔助，不是把判斷外判出去。'
        ],
        outcome: '當你覺得結果奇怪，先回到最早出錯的步驟，而不是直接改報告文字。'
      },
      graph: {
        code: 'GRAPH',
        title: '知識圖譜把自然語言變成可檢查結構',
        summary: 'Murmura 會將 seed text 轉成節點與邊：誰影響誰、哪個資源被爭奪、哪條因果鏈正在形成。這是後續 agent factory 與 GraphRAG 的地基。',
        steps: [
          'EntityExtractor 找出明示節點與關係。',
          'Alias map 合併同一實體的不同叫法。',
          'ImplicitStakeholderService 補上間接受影響的人與組織。',
          '圖譜快照會在模擬期間跟隨行動更新。'
        ],
        checks: [
          '節點應該有足夠多樣性，不應只剩主角。',
          '邊的方向要符合因果或互動方向。',
          '隱含角色應該能從 seed text 推出，而不是靠外部常識亂補。',
          '如果要預測某指標，圖上應該有能影響該指標的節點。'
        ],
        outcome: '圖譜是你最早、成本最低的品質控制點；看不懂圖，就不要急著按開始模擬。'
      },
      actors: {
        code: 'AGENTS',
        title: '代理人不是群眾貼紙，而是有記憶與偏好的決策者',
        summary: '每個代理人會有身份、人格、認知指紋、記憶、平台身份與信任關係。重點是多樣性：不同層級、利益、資訊來源會產生不同反應。',
        steps: [
          'KGAgentFactory 從圖譜節點挑選可行角色。',
          '當 target count 大於明示角色，系統會生成背景代理人。',
          '代理人會得到 Big Five、依附風格、政治或價值傾向。',
          '記憶會寫入 LanceDB，供後續訪談與決策檢索。'
        ],
        checks: [
          '不要只看代理人數量，要看角色分佈是否合理。',
          '關鍵持份者應該被標記為 stakeholder，而不是背景噪音。',
          '平台身份要反映語境：同一代理人在不同平台可以有不同行為。',
          '如果代理人過於同質，湧現結果會變得假穩定。'
        ],
        outcome: '大型模擬不一定更準；有代表性、有衝突、有資訊差的代理人組合才重要。'
      },
      simulation: {
        code: 'SIM',
        title: '模擬觀察的是互動後的形狀',
        summary: 'Step 3 會按輪次運行代理人：發言、決策、信念更新、情緒變化、派系形成、回音室、宏觀回饋與 moderation event。這些不是靜態摘要，而是互動後的路徑。',
        steps: [
          '每輪先整理 feed ranking 與世界事件。',
          '代理人根據記憶、關係、信念與平台身份行動。',
          '信念以 Bayesian update 與 embedding propagation 更新。',
          '每隔幾輪計算派系、極化、病毒式傳播、宏觀狀態與 tipping point。'
        ],
        checks: [
          '留意趨勢轉折點，而不是只看平均值。',
          '比較派系之間的行動差異。',
          '看 shock 之後是否出現合理的延遲與連鎖反應。',
          '如果 Python 版本不兼容，UI 會降級並停在環境設定後。'
        ],
        outcome: '一次模擬是一條路徑；要講穩健性，就要看 ensemble、fork 或反事實分支。'
      },
      probability: {
        code: 'DIST',
        title: '讀概率分佈，不要只讀單點預測',
        summary: 'Murmura 的輸出應該用分佈來讀：p50 是中位數，p10-p90 是寬範圍不確定區間，分支之間的差距代表模型認為未來可能分叉。',
        steps: [
          '先看 p50，理解系統最中間的路徑。',
          '再看 p10-p90，判斷尾部風險有幾闊。',
          '比較不同 preset、shock、fork 的分佈是否一致。',
          '用 Monte Carlo 與 Swarm Ensemble 檢查敏感度。'
        ],
        checks: [
          '70% 不是必然，只是長期頻率語言。',
          '窄區間不一定代表真準，可能代表假設過窄。',
          '分佈偏斜時，平均值可能誤導。',
          '決策要看損失函數，不只看最大概率事件。'
        ],
        outcome: '真正有用的問題不是「會不會發生」，而是「在什麼條件下、以什麼代價、以多大不確定性發生」。'
      },
      uncertainty: {
        code: 'RISK',
        title: '信心來自可追溯性，不來自語氣肯定',
        summary: '模型可以講得很肯定，但你要看的是真正支撐：輸入質量、圖譜覆蓋、代理人多樣性、樣本路徑數、工具證據與歷史校準。',
        steps: [
          '辨認不確定性來源：文本缺口、模型假設、LLM 隨機性、外部 shock。',
          '看報告引用的工具與數據是否能支撐結論。',
          '查看不同分支是否收斂或分裂。',
          '把高風險結論轉成需要驗證的假設。'
        ],
        checks: [
          '高信心但低證據密度，是危險訊號。',
          '結果若只由少數代理人推動，要查是否代表性不足。',
          '對突發事件的預測應該保持保守。',
          '透明寫出限制，比輸出漂亮答案更重要。'
        ],
        outcome: '可信預測不是沒有不確定性，而是知道不確定性在哪裡。'
      },
      report: {
        code: 'REPORT',
        title: '報告是可檢查的推理產物',
        summary: '報告階段會以 ReACT 流程組裝：先列大綱，再用 XAI 工具查時間線、派系、指標、信念、證據，最後生成可分享或輸出的分析。',
        steps: [
          'Report Orchestrator 先建立章節計劃。',
          '每個章節調用對應工具查詢 DB 與時間線。',
          'LLM 整合證據、圖表與限制。',
          '報告可輸出 PDF，並用 share token 分享。'
        ],
        checks: [
          '結論要能追到模擬事件或圖譜證據。',
          '不要接受沒有對照分支的強因果說法。',
          '看報告是否清楚區分觀察、推斷與建議。',
          '重新生成報告前，先確認模擬 session 未被清理。'
        ],
        outcome: '好報告應該幫你追問，而不是終止思考。'
      },
      interaction: {
        code: 'ASK',
        title: '互動階段用來審訊模型，不是聊天消遣',
        summary: 'Step 5 可以訪談代理人、問 Narrative Analyst、追查某次行動背後的記憶，也可以提出 what-if 假設，比較代理人是否改變立場。',
        steps: [
          '選擇報告分析師或指定代理人。',
          '針對某輪事件、某個派系或某條因果鏈提問。',
          '要求代理人引用自己的記憶與信念變化。',
          '注入假設衝擊，觀察答案是否一致。'
        ],
        checks: [
          '問題要具體：問輪次、指標、角色、行動。',
          '代理人的回答是角色內推理，不等於事實。',
          '如果回答與報告矛盾，要回查 timeline 與 DB 證據。',
          '用互動找風險，不要只找支持自己立場的句子。'
        ],
        outcome: '把互動當成審計工具：問「你點知？」通常比問「你覺得點？」更有價值。'
      },
      limits: {
        code: 'LIMITS',
        title: '模型邊界要寫在決策前面',
        summary: 'Murmura 受 seed text、LLM provider、資料延遲、模擬 preset、OASIS runtime 與成本上限影響。知道邊界，才知道結果可以用到哪裡。',
        steps: [
          '檢查 seed text 是否包含足夠背景與時間範圍。',
          '確認 Settings 的 step-specific 模型與 API key 可用。',
          '查看成本、並行、agent count 與 rounds 是否符合用途。',
          '清楚標示哪些資料是實時、延遲、模擬生成或 LLM 推斷。'
        ],
        checks: [
          '不要用 demo mode 結果做高風險決策。',
          '法律、醫療、投資與安全用途需要外部專家驗證。',
          '輸入資料含 prompt injection 時，必須先經安全清洗。',
          '舊 session 的結果可能不反映最新資料或模型設定。'
        ],
        outcome: '最專業的用法，是把 Murmura 放在決策流程入面做壓力測試，而不是把它當成決策者。'
      }
    },
    glossary: [
      { term: 'Seed Text', desc: '你投放入系統的原始場景、文件或問題背景。' },
      { term: 'Knowledge Firewall', desc: '提示詞限制 LLM 只根據 seed text 推理，避免偷用未來知識。' },
      { term: 'Tipping Point', desc: '系統分佈突然轉向或分叉的臨界點。' },
      { term: 'p10-p90', desc: '80% 模擬結果落入的區間，用來看尾部風險與不確定性。' },
      { term: 'Stakeholder', desc: '對結果有實質影響或會被結果影響的角色。' },
      { term: 'What-If Fork', desc: '在某輪注入 shock 後建立的新時間線，用來比較反事實結果。' }
    ]
  },
  home: {
    eyebrow: '通用預測工作台',
    subtitle: '通用預測引擎',
    description: '投放任何種子文字——新聞、劇本、地緣政治事件——AI 自動構建世界、生成代理人並開始模擬。結合多智能體系統、知識圖譜與宏觀預測，預見集體行為。',
    consoleTitle: 'Prediction Console',
    consoleStatus: '系統狀態',
    consoleStatusLive: '可用',
    consoleSignal: 'Clean-room UI · 5-step workflow',
    pipelineTitle: '五步控制流',
    examplesTitle: '示例場景',
    sampleWar: '地緣衝突升級後的能源市場反應',
    sampleFiction: '小說世界中主要陣營的集體選擇',
    sampleCompany: '新競爭者進入後的 B2B 供應鏈反應',
    inputLabel: 'INPUT',
    fileLabel: 'SEED FILE',
    seedLabel: 'SEED TEXT',
    questionLabel: 'QUESTION',
    presetLabel: 'RUN PRESET',
    toolsTitle: '工程工具',
    domainPacks: '領域包',
    metrics: {
      zeroConfig: '零配置',
      kg: 'GraphRAG',
      oasis: 'OASIS',
      react: 'ReACT'
    },
    workflow: {
      graph: '抽取實體、關係與隱含持份者',
      env: '生成代理人、平台身份與場景配置',
      sim: '運行多智能體模擬與湧現 hooks',
      report: '以 XAI 工具生成可追溯報告',
      interact: '訪談代理人並探索 What-If 分支'
    },
    startTitle: '立即開始預測',
    startSubtitle: '上傳文件或輸入種子文字，AI 自動構建世界並開始模擬',
    dropLabel: '拖放文件至此，或點擊選擇',
    dropHint: '支援 PDF、TXT、Markdown · 最大 10 MB',
    or: '或',
    textareaPlaceholder: '輸入場景描述，例如：聯準會宣布升息200個基點，全球股市出現恐慌性拋售...',
    questionPlaceholder: '（選填）你想預測什麼？例如：哪個陣營最終會佔主導？社會情緒走向如何？',
    launchBtn: '一鍵預測',
    launching: '啟動中...',
    customDomain: '自定義領域包',
    dataConnector: '數據連接器',
    godView: '上帝視角',
    presets: {
      fast: '快速',
      fastHint: '100 位代理人 · 15 輪模擬 (~2 分鐘)',
      standard: '標準',
      standardHint: '300 位代理人 · 20 輪模擬 (~8 分鐘)',
      deep: '深度',
      deepHint: '500 位代理人 · 30 輪模擬 (~20 分鐘)'
    },
    errors: {
      format: '不支援 {ext} 格式，請上傳 PDF、TXT 或 Markdown',
      size: '檔案超過 10 MB 上限',
      launch: '啟動失敗，請重試'
    }
  },
  onboarding: {
    skip: '跳過',
    next: '下一步',
    finish: '完成',
    steps: {
      scenario: { title: '選擇預測場景', desc: '從首頁選擇一個社會議題作為模擬預測的起點。' },
      graph: { title: '知識圖譜', desc: '系統會自動建立知識圖譜，展示議題中的因果關係。' },
      simulation: { title: '運行模擬', desc: '觀察 AI 代理人如何互動、做決策、形成社會趨勢。' }
    }
  },
  landing: {
    nav: {
      howItWorks: '運作原理',
      features: '核心功能',
      launch: '啟動引擎 →'
    },
    hero: {
      eyebrow: '通用預測引擎',
      title: '投放任何文字。',
      titleAccent: '模擬任何世界。',
      sub: '餵給 Murmura 一句話、一份文件或一個場景 —— 它會自動構建知識圖譜、生成代理人、運行模擬並預測集體結果。',
      cta: '開始預測',
      workspace: '工作區',
      stats: {
        agents: '單次運行代理人',
        macro: '宏觀經濟指標',
        monteCarlo: '蒙地卡羅試驗',
        xai: '可解釋 AI 工具'
      }
    },
    workflow: {
      label: '運作原理',
      title: '五步工作流',
      steps: {
        graph: { label: '圖譜', title: '知識圖譜', desc: '種子文字 → 實體提取 → 因果網絡自動構建' },
        env: { label: '環境', title: '環境設定', desc: '代理人工廠依據圖譜節點生成配置，無需手動設定' },
        sim: { label: '模擬', title: '動態模擬', desc: 'OASIS 多智能體引擎運行，完整捕捉湧現行為' },
        report: { label: '報告', title: 'ReACT 報告', desc: '三階段 LLM：大綱 → 多路工具調用 → 文檔組裝' },
        interact: { label: '互動', title: '深度互動', desc: '訪談代理人、注入衝擊、開拓「What-If」分支場景' }
      }
    },
    features: {
      label: '引擎能力',
      title: '我們的核心功能',
      list: {
        universal: { title: '通用模式', desc: '支援任何種子文字 —— 新聞、小說、地緣政治。引擎自動推斷代理人、決策、指標與衝擊。' },
        kg: { title: '知識圖譜', desc: 'GraphRAG 追蹤實體關係與因果鏈。每 5 輪生成快照，隨互動持續演化。' },
        emergence: { title: '湧現引擎', desc: '派系形成、臨界點、同溫層、病毒式傳播 —— 全部為自主湧現，而非預設腳本。' },
        monteCarlo: { title: '蒙地卡羅', desc: '100 次 LHS + t-Copula 採樣。Wilson 得分置信區間。支援高達 10,000 次隨機試驗。' },
        macro: { title: '宏觀回饋', desc: '每輪更新 11 個宏觀指標。代理人的微觀決策即時回饋至宏觀狀態。' },
        scenarios: { title: '場景分支', desc: '在任何輪次分叉模擬。並排比較不同時間線的演化結果。' }
      }
    },
    useCases: {
      label: '應用領域',
      title: '適用於任何領域',
      list: {
        geopolitics: { tag: '地緣政治', desc: '台海局勢演變、伊以衝突模擬、貿易戰連鎖反應' },
        finance: { tag: '金融', desc: '聯準會升息外溢效應、加密貨幣恐慌、企業競爭對抗' },
        society: { tag: '社會', desc: '政策影響建模、社會運動動態、人口結構變遷' },
        fiction: { tag: '虛構作品', desc: '《紅樓夢》、哈利波特、任何敘事世界' }
      }
    },
    cta: {
      label: '準備好開始模擬了嗎？',
      title: '投放你的第一個場景',
      sub: '無需配置。粘貼任何文字，剩下的交給引擎處理。',
      btn: '啟動引擎 →'
    },
    footer: {
      desc: '通用預測引擎 · 基於代理人的模擬技術',
      copy: '構建技術：FastAPI · Vue 3 · OASIS · LanceDB'
    }
  },
  process: {
    nav: {
      steps: {
        graph: { label: '圖譜構建', navLabel: 'GRAPH' },
        env: { label: '環境搭建', navLabel: 'ENV' },
        sim: { label: '開始模擬', navLabel: 'SIM' },
        report: { label: '報告生成', navLabel: 'REPORT' },
        interact: { label: '深度交互', navLabel: 'INTERACT' }
      },
      expressBadge: '⚡ 快速模式 · 已自動配置'
    },
    workbench: {
      subtitle: '從種子文本到可追溯報告的五步預測流水線',
      session: 'SESSION',
      graph: 'GRAPH',
      preset: 'PRESET',
      engine: 'ENGINE',
      unavailable: 'LIMITED',
      ready: 'READY',
      locked: 'LOCKED',
      done: 'DONE',
      active: 'ACTIVE'
    },
    errors: {
      graphFirst: '請先完成圖譜構建',
      envFirst: '請先完成環境設置並啟動模擬',
      simFirst: '模擬完成後才可生成報告',
      reportFirst: '請先生成報告',
      engineUnavailable: '模擬引擎不可用 — 請使用 Docker 以獲得完整功能',
      engineUnavailableDetail: '模擬引擎不可用 — 請使用 Docker 以獲得完整功能。流程將在環境設定後停止。'
    }
  },
  step2: {
    badges: {
      experimental: '實驗'
    },
    actions: {
      creating: '建立中...',
      start: '開始模擬'
    }
  },
  settings: {
    header: {
      title: '設定',
      subtitle: '管理 API 金鑰、模型選擇及系統偏好設定'
    },
    tabs: {
      api: {
        title: 'API 金鑰',
        desc: '設定各 LLM 服務提供商的 API 金鑰。金鑰已加密儲存，顯示時僅顯示尾部 4 碼。',
        empty: '— 未設定 —',
        testing: '⏳ 測試中…',
        test: '測試',
        save: '儲存',
        verifying: '⏳ 正在驗證金鑰…',
        connFailed: '連線失敗'
      },
      model: {
        title: '模型選擇',
        desc: '為每個工作流步驟獨立設定 LLM 模型。儲存後即時生效，無需重啟伺服器。',
        quickApply: '快速套用：',
        globalFallback: '全域預設（各步驟未設定時使用）',
        models: {
          sync: '同步模型',
          syncing: '同步中…',
          chooseProvider: '先選擇 Provider',
          unsupported: '此 Provider 暫未支援自動模型清單，可手動輸入 model id',
          notLoaded: '尚未同步模型清單；可先儲存/測試 API key，或按同步模型',
          loading: '正在讀取模型清單…',
          loaded: '已載入 {count} 個模型；亦可手動輸入未列出的 model id'
        },
        steps: {
          useGlobal: '使用全域預設',
          fillBoth: '請填寫 Provider 和 Model',
          step1: { label: 'Step 1：知識圖譜建構', hint: '建議使用速度快的模型（如 deepseek-v3），此步驟呼叫頻繁' },
          step2: { label: 'Step 2：環境設置', hint: '建議使用推理能力強的模型，用於代理人格設定與場景分析' },
          step3: { label: 'Step 3：模擬運行', hint: '主力模型用於關鍵角色，精簡模型用於背景代理（節省費用）' },
          step4: { label: 'Step 4：報告生成', hint: '建議使用長文生成能力強的模型（如 Gemini Pro、GPT-4o）' },
          step5: { label: 'Step 5：互動分析', hint: '建議使用對話能力強的模型，用於 Interview Engine' },
        },
        agent: {
          title: '代理決策 LLM（全域）',
          providerHint: '代理思考、決策、發文所用的 LLM 提供商',
          main: 'Agent Model（主力）',
          mainHint: '一般 background agents 使用此較便宜的模型（可選）',
          lite: 'Agent Model（精簡）',
          liteHint: '一般 background agents 使用此較便宜的模型（可選）'
        },
        report: {
          title: '報告生成 LLM（全域）',
          providerHint: '最終報告、摘要、圖表分析所用的 LLM',
          model: '報告模型 (Report Model)',
          modelHint: '留空則使用該提供商的預設模型'
        }
      },
      sim: {
        title: '模擬預設',
        desc: '設定新建模擬時的預設參數。',
        preset: '預設 Preset',
        agents: '預設代理數量',
        agentsUnit: '位代理人',
        agentsHint: '建立新模擬時的預設代理數量（5–500）',
        concurrency: '並行限制 (Concurrency)',
        concurrencyHint: '同時執行 LLM 請求的最大數量。建議 30–80',
        domain: '預設 Domain Pack',
        domainHint: '新模擬套用的預設 Domain Pack ID'
      },
      ui: {
        title: '介面偏好',
        desc: '以下偏好儲存於本機（localStorage），即時生效。',
        lang: 'UI 語言',
        itemsPerPage: '每頁顯示數量',
        autoOpen: '模擬完成後自動開啟報告',
        autoOpenHint: '完成 simulation 後自動跳轉至報告頁面'
      },
      data: {
        title: '資料來源',
        desc: '設定外部數據源 API 金鑰及整合選項。',
        empty: '— 未設定 —',
        test: '測試',
        save: '儲存',
        verifying: '⏳ 正在驗證…',
        ref: '來自',
        fred: 'FRED API 金鑰',
        fredHint: '來自 <a href="https://fred.stlouisfed.org/docs/api/api_key.html" target="_blank" rel="noopener">St. Louis Fed</a>，用於獲取宏觀經濟數據',
        externalFeed: '啟用外部數據源',
        externalFeedHint: '啟用後系統將從 FRED、World Bank 等源定時更新數據',
        refreshInterval: '更新頻率',
        seconds: '秒',
        refreshHint: '每次自動更新的間隔（300–86400 秒）'
      }
    }
  },
  workspace: {
    title: '工作區',
    subtitle: '所有預測模擬 Session',
    adminBtn: '效能管理',
    newBtn: '+ 新預測',
    loading: '載入中...',
    retry: '重試',
    empty: {
      title: '尚未有預測',
      description: '建立你的第一個社會模擬預測'
    },
    status: {
      completed: '已完成',
      running: '運行中',
      failed: '失敗',
      pending: '等待中',
      created: '已建立'
    },
    meta: {
      agents: '位代理人',
      rounds: '輪模擬'
    },
    evidence: '證據搜尋',
    loadMore: '載入更多'
  }
}
