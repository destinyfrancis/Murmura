export default {
  nav: {
    home: 'Home',
    workspace: 'Workspace',
    learn: 'Learn',
    about: 'About',
    report: 'Reporting',
    godView: 'God View',
    settings: 'Settings',
  },
  godView: {
    header: {
      terminal: 'GOD VIEW TERMINAL',
      selectSession: '-- Select Session --',
      loading: 'LOADING...',
      refresh: 'REFRESH',
      autoOn: 'AUTO ON',
      autoOff: 'AUTO OFF',
      autoDelayed: 'AUTO (DELAYED)'
    },
    status: {
      signals: 'SIGNALS',
      active: 'active',
      buyYes: 'BUY YES',
      buyNo: 'BUY NO',
      hold: 'HOLD',
      contracts: 'CONTRACTS',
      lastRefreshed: 'Last'
    },
    tabs: {
      main: 'Market Signals',
      ensemble: 'Ensemble Pred',
      scenarios: 'Scenario Comparison',
      sentiment: 'Sentiment Heatmap'
    },
    panels: {
      contracts: {
        title: 'POLYMARKET CONTRACTS',
        loading: 'Fetching contracts...',
        empty: 'No contracts matched for this session.'
      },
      signals: {
        title: 'TRADING SIGNALS',
        loading: 'Computing signals from agent consensus...',
        empty: 'No signals generated yet. Ensure simulation has completed at least 5 rounds.'
      },
      consensus: {
        title: 'AGENT CONSENSUS',
        sentimentTrend: 'SENTIMENT TREND',
        signalBreakdown: 'SIGNAL BREAKDOWN',
        recentDecisions: 'RECENT DECISIONS',
        noData: 'No data',
        awaiting: 'Awaiting agent decisions...'
      },
      feed: {
        title: 'LIVE AGENT FEED',
        empty: 'No agent activity yet.',
        posts: 'posts'
      }
    },
    placeholders: {
      selectSession: 'Select a simulation session to begin',
      godViewDesc: 'The God View Terminal shows real-time Polymarket trading signals derived from agent consensus'
    }
  },
  interaction: {
    welcome: 'Welcome to Deep Interaction mode. You can ask questions about the report or chat with individual agents.',
    noResponse: '(No response)',
    sendFailed: 'Send failed:',
    settings: {
      title: 'Chat Settings',
      target: 'Chat Target',
      analyst: 'Report Analyst',
      agent: 'Specific Agent',
      selectAgent: 'Select Agent',
      selectPlaceholder: 'Please select...',
      whatIf: 'What-If Parameters',
      whatIfHint: 'Describe hypothetical scenarios in your chat, e.g., "What if unemployment rises to 8%"'
    },
    chat: {
      you: 'You',
      ai: 'AI',
      system: 'System',
      error: 'Error',
      placeholder: 'Type your question...',
      sending: 'Sending...',
      send: 'Send'
    }
  },
  lessons: {
    overview: {
      traditional: {
        title: 'Traditional Polling',
        points: [
          'Ask 1,000 people their thoughts',
          'Static snapshot — one-time',
          'Ignores social impact',
          'Cannot simulate policy changes'
        ],
        verdict: 'Limited'
      },
      murmura: {
        title: 'Murmura',
        points: [
          'Simulate 500 AI agent interactions',
          'Dynamic evolution — 30+ rounds',
          'Echo Chamber + Trust Networks',
          'Real-time policy shock injection'
        ],
        verdict: 'Emergent Prediction'
      },
      text1: 'Murmura does not ask people "what are you thinking," but uses AI agents to simulate real social interaction processes. Each agent has its own personality, memory, and trust circle; they influence each other, and eventually, group trends <strong>emerge</strong>.',
      text2: 'The metrics we track include: property price confidence, migration intent, consumption patterns, political polarization, etc.'
    },
    uncertainty: {
      intro: "Murmura's prediction uncertainty comes from four main sources. Click each source to learn more:",
      closing: 'Transparently presenting uncertainty is a core principle of responsible AI prediction. Murmura is not an "oracle" but a tool to help think about multiple possible futures.',
      sources: {
        behavior: { label: 'Agent Behavior Randomness', detail: 'Each AI agent\'s LLM decision has inherent randomness that cannot be fully controlled.' },
        macro: { label: 'Macro Data Error', detail: 'Macro data like GDP and unemployment rates have measurement errors and revisions, directly affecting initial conditions.' },
        model: { label: 'Model Structure Assumptions', detail: 'Parameters like consumption functions and trust decay rates are estimated from calibration data, which have statistical uncertainty.' },
        shocks: { label: 'External Shocks Unpredictability', detail: 'Exogenous shocks like geopolitical events and natural disasters cannot be included in the model in advance.' }
      }
    },
    kg: {
      intro: 'Knowledge Graphs break down complex issues into <strong>entities</strong> (nodes) and <strong>relationships</strong> (edges). Hover over nodes to see descriptions.',
      closing: 'During simulation, agent actions update the edge weights on the graph — reflecting changes in the strength of causal relationships.',
      types: {
        economic: 'Economic',
        person: 'Person',
        policy: 'Policy',
        organization: 'Organization',
        social: 'Social',
        location: 'Location'
      },
      nodes: {
        hibor: 'HIBOR Rate',
        mortgage: 'Mortgage Rate',
        prices: 'Property Indices',
        buyers: 'First-time Buyers',
        tax: 'Stamp Duty',
        bank: 'HSBC',
        hardlife: 'Affordability',
        migration: 'Migration Wave',
        shatin: 'Sha Tin',
        fed: 'The Fed'
      }
    },
    boids: {
      intro: 'Agent behavior follows three simple rules, similar to bird flocking (Boids theory):',
      rules: {
        alignment: { title: 'Alignment', desc: 'Heading in the same direction as neighbors (Social Consensus).' },
        cohesion: { title: 'Cohesion', desc: 'Moving towards the average position of neighbors (Trust Building).' },
        separation: { title: 'Separation', desc: 'Avoiding getting too close to conflicting entities (Echo Chambers).' }
      },
      closing: 'No single bird has the concept of a "flock formation" — yet the formation emerges naturally. This is <strong>emergence</strong>.',
      murmura: 'Murmura works the same way — each agent makes decisions based on its own personality and memory, but overall, predictable social trends emerge.'
    },
    ner: {
      intro: 'Each piece of seed text undergoes the following processing pipeline, eventually becoming nodes and edges in the Knowledge Graph:',
      steps: ['Raw Text', 'Tokenization', 'NER Recognition', 'Relation Extraction', 'KG Node'],
      example: {
        label: 'Example:',
        text: 'The <strong>Fed</strong> announced a <strong>rate hike</strong> of 0.25%, affecting the <strong>HK property market</strong>',
        org: 'Fed (Org)',
        hike: 'Rate Hike (Event)',
        market: 'HK Property (Economic)',
        announced: 'announced',
        affecting: 'affecting'
      },
      closing: 'This process is driven by DeepSeek V3.2, automatically identifying entity types and causal relationships to build a structured knowledge representation.'
    },
    shocks: {
      intro: 'Policy shocks are the "stress tests" of the Murmura system. You can inject the following events into the running simulation:',
      events: {
        interest_rate: { title: 'Interest Rate Hike', desc: 'Sudden 1% increase in mortgage rates' },
        tax: { title: 'Stamp Duty Remove', desc: 'Government removes all property stamp duties' },
        immigration: { title: 'Migration Policy Change', desc: 'New points-based immigration system launched' }
      },
      text: 'When a shock is injected, agents re-evaluate their beliefs and trust networks, leading to a "cascade" effect throughout the entire system.'
    },
    percentiles: {
      intro: 'Murmura does not just output a single prediction line, but an entire probability distribution. Drag the slider to adjust scenario intensity:',
      chartLabel: 'Property Price Confidence Index Forecast',
      mild: 'Mild Shock',
      extreme: 'Extreme Shock',
      intensity: 'Scenario Intensity',
      p10_90: 'p10–p90',
      p25_75: 'p25–p75',
      p50: 'p50 (Median)',
      quiz: {
        q1: 'Question 1: What does p50 represent?',
        q1_opts: [
          { value: 'p50', label: 'Median Forecast' },
          { value: 'avg', label: 'Average' },
          { value: 'best', label: 'Best Case' }
        ],
        q1_correct: 'Correct! p50 is the median; half of the simulation results are higher and half are lower.',
        q1_wrong: 'Incorrect. p50 is the median (50th percentile), not the average.',
        q2: 'Question 2: What does a wider p10-p90 interval represent?',
        q2_opts: [
          { value: 'wide', label: 'Higher Uncertainty' },
          { value: 'certain', label: 'More Accurate' },
          { value: 'same', label: 'Same Results' }
        ],
        q2_correct: 'Correct! A wider interval reflects higher prediction uncertainty.',
        q2_wrong: 'Incorrect. A wider interval means higher uncertainty, not more accuracy.'
      }
    },
    challenges: {
      intro: 'Simulation results should not be accepted blindly. Here is a 5-step critical assessment checklist — check each step as you complete it:',
      allChecked: 'All complete! You have mastered the method of critical model assessment.',
      reset: 'Reset',
      closing: 'Developing these 5 habits will help you avoid over-reliance on model outputs and make more informed judgments.',
      assumptions: { label: 'Check Assumptions', detail: 'Are the model\'s premises reasonable?' },
      history: { label: 'Compare History', detail: 'How did similar situations play out in the past?' },
      boundary: { label: 'Boundary Test', detail: 'What happens with extreme parameters?' },
      counterfactual: { label: 'Counterfactual Reasoning', detail: 'How would results change if a factor was removed?' },
      omission: { label: 'Find Omissions', detail: 'Are there any critical factors missing?' }
    },
    mistakes: {
      intro: 'Avoid these common pitfalls when interpreting Murmura simulations:',
      list: [
        { wrong: 'The model says 70% chance of falling, so it will definitely fall', correct: 'A 70% chance means it happens about 7 times out of 10' },
        { wrong: 'p50 prediction is the most accurate', correct: 'p50 is the median; real results may fall anywhere between p10-p90' },
        { wrong: 'The more agents, the more accurate', correct: 'Agent diversity is more important than quantity' },
        { wrong: 'The model predicted a Black Swan event', correct: 'Models can only capture known risks; true Black Swans are unpredictable' },
        { wrong: 'Different results for two simulations mean the model is unreliable', correct: 'Randomness is a feature of the model, not a flaw' }
      ]
    },
    dataSources: {
      intro: 'Murmura combines high-frequency market data with low-frequency statistical indicators to ground its simulations:',
      category: 'Category',
      items: 'Key Items',
      frequency: 'Frequency',
      lag: 'Data Lag',
      gov: { category: 'Gov Statistics', items: ['Census', 'Employment', 'Retail Sales'], frequency: 'Monthly', lag: '~2 months' },
      finance: { category: 'Financial Markets', items: ['HSI Index', 'Sector Indices', 'Volume'], frequency: 'Real-time', lag: '< 15 mins' },
      rates: { category: 'Interest Rates', items: ['HIBOR', 'Fed Rate', 'USD/HKD'], frequency: 'Daily', lag: '1 day' },
      social: { category: 'Social Media', items: ['RTHK News', 'Forum Posts', 'Sentiment'], frequency: 'Hourly', lag: '< 1 hour' },
      macro: { category: 'Macro Economy', items: ['China GDP', 'CPI', 'Exports'], frequency: 'Quarterly', lag: '~3 months' }
    },
    meta: {
      t0: 'What does system predict?',
      t1: 'What is Emergence?',
      t2: 'KG Introduction',
      t3: 'From Evidence to Structure',
      t4: 'From Scenario to Outcome',
      t5: 'Reading Probabilities',
      t6: 'Confidence & Uncertainty',
      t7: 'Challenging the Model',
      t8: 'Common Mistakes',
      t9: 'Data Sources & Limits'
    }
  },
  learn: {
    eyebrow: 'Operator Manual',
    title: 'From seed text to traceable forecasts',
    subtitle: 'This is not a product brochure. It is an operator manual for understanding how Murmura reads a scenario, builds a knowledge graph, generates agents, runs OASIS simulations, interprets probability reports, and challenges model output.',
    metricsLabel: 'Learning summary',
    indexLabel: 'Lesson index',
    glossaryLabel: 'Quick Reference',
    glossaryTitle: 'Terms to know before reading results',
    metrics: [
      { value: '10', label: 'Lessons' },
      { value: '05', label: 'Workflow steps' },
      { value: '18', label: 'XAI tools' },
      { value: 'p10-p90', label: 'Uncertainty band' }
    ],
    workflow: [
      { label: 'Graph', desc: 'Break raw text into entities, relations, hidden stakeholders, and initial metrics.' },
      { label: 'Env', desc: 'Convert the graph into agents, platform identities, decision spaces, and scenario config.' },
      { label: 'Sim', desc: 'Run round-by-round decisions, belief updates, faction formation, and macro feedback.' },
      { label: 'Report', desc: 'Use explainable tools to inspect evidence, generate reports, export PDF, or share a link.' },
      { label: 'Interact', desc: 'Interview agents, test assumptions, inject shocks, and compare branch timelines.' }
    ],
    blocks: {
      whatHappens: 'What the system actually does',
      howToRead: 'How you should interpret it',
      operatorRule: 'Operator rule'
    },
    modules: {
      overview: {
        code: 'START',
        title: 'Murmura forecasts collective response, not a single answer',
        summary: 'After you provide seed text, Murmura turns it into a runnable social, corporate, market, or narrative world. The point is not to ask an LLM for an answer; it is to let different agents influence one another inside the same world.',
        steps: [
          'Read the text while preserving the timeline and context you provided.',
          'Extract explicit actors, events, places, organizations, resources, and conflicts.',
          'Infer stakeholders who are affected but not directly named.',
          'Let agents act round by round and observe how group trends emerge.'
        ],
        checks: [
          'Treat output as a map of possible futures, not a prophecy.',
          'Check whether agents, metrics, and shocks match the source text.',
          'Use report evidence and counterfactual branches to test robustness.',
          'If the seed text is narrow, the simulated world will be narrow too.'
        ],
        outcome: 'The strongest workflow is to define the question first, then let the system construct the world. A headline alone rarely contains enough causal structure.'
      },
      workflow: {
        code: 'FLOW',
        title: 'The five-step workflow is one prediction pipeline',
        summary: 'Every step leaves state behind. You can pause at graph review, rebuild the environment, change presets, regenerate reports, or question agents during the interaction phase.',
        steps: [
          'Step 1 builds the KG by extracting entities, relations, and hidden stakeholders.',
          'Step 2 creates agent profiles, platform identities, initial memories, and decision spaces.',
          'Step 3 runs the OASIS subprocess and records actions, beliefs, and events by round.',
          'Step 4 generates a ReACT report using XAI tools over data and timelines.',
          'Step 5 supports interviews, evidence checks, and what-if shock injection.'
        ],
        checks: [
          'If the graph is wrong, every later step inherits that error.',
          'The environment is the entrance to agent worldviews and deserves sampling.',
          'In simulation, inspect trends, divergence, and tipping points, not only the final round.',
          'A report is decision support, not delegated judgment.'
        ],
        outcome: 'When a result feels strange, return to the earliest step where the mistake could have entered.'
      },
      graph: {
        code: 'GRAPH',
        title: 'The knowledge graph makes natural language inspectable',
        summary: 'Murmura converts seed text into nodes and edges: who influences whom, what resource is contested, and which causal chain is forming. This is the foundation for the agent factory and GraphRAG.',
        steps: [
          'EntityExtractor finds explicit nodes and relations.',
          'Alias mapping merges different names for the same entity.',
          'ImplicitStakeholderService adds indirectly affected actors.',
          'Graph snapshots evolve during simulation as agents act.'
        ],
        checks: [
          'Nodes should be diverse enough, not just the obvious protagonists.',
          'Edge direction should match causal or interaction direction.',
          'Implied actors should be inferable from the seed text, not invented from unrelated knowledge.',
          'If you forecast a metric, the graph should include things that can move that metric.'
        ],
        outcome: 'The graph is the earliest and cheapest quality-control point. If the graph is not credible, do not rush into simulation.'
      },
      actors: {
        code: 'AGENTS',
        title: 'Agents are decision-makers with memory and preferences',
        summary: 'Each agent can carry identity, personality, cognitive fingerprint, memory, platform identity, and trust relations. Diversity matters: layers of interest, information, and exposure create different reactions.',
        steps: [
          'KGAgentFactory chooses viable roles from graph nodes.',
          'When target count exceeds explicit roles, the system creates background agents.',
          'Agents receive Big Five traits, attachment style, and value or political orientation.',
          'Memories are written to LanceDB for later decisions and interviews.'
        ],
        checks: [
          'Do not look only at agent count; inspect role distribution.',
          'Key stakeholders should be marked as stakeholders, not background noise.',
          'Platform identity should match context: the same agent may behave differently on different platforms.',
          'Overly homogeneous agents produce falsely stable emergence.'
        ],
        outcome: 'Bigger is not automatically better. Representative, conflicting, information-diverse agents are what make a run useful.'
      },
      simulation: {
        code: 'SIM',
        title: 'Simulation shows the shape after interaction',
        summary: 'Step 3 runs agents by round: posts, decisions, belief updates, emotional shifts, faction formation, echo chambers, macro feedback, and moderation events. It is a path, not a static summary.',
        steps: [
          'Each round begins with feed ranking and world-event context.',
          'Agents act based on memory, relations, beliefs, and platform identity.',
          'Beliefs update through Bayesian revision and embedding propagation.',
          'Periodic hooks compute factions, polarization, virality, macro state, and tipping points.'
        ],
        checks: [
          'Watch trend inflections rather than only averages.',
          'Compare behavior across factions.',
          'After a shock, look for plausible delay and cascade effects.',
          'If Python is incompatible, the UI degrades and stops after environment setup.'
        ],
        outcome: 'One simulation is one path. Robust claims need an ensemble, fork, or counterfactual branch.'
      },
      probability: {
        code: 'DIST',
        title: 'Read probability distributions, not just point forecasts',
        summary: 'Murmura output should be read as a distribution: p50 is the median path, p10-p90 is a wide uncertainty band, and branch gaps show where the model thinks the future may split.',
        steps: [
          'Read p50 first to understand the middle path.',
          'Read p10-p90 to judge tail risk.',
          'Compare distributions across presets, shocks, and forks.',
          'Use Monte Carlo and Swarm Ensemble outputs to check sensitivity.'
        ],
        checks: [
          '70% is not certainty; it is frequency language.',
          'A narrow interval is not always accuracy; it may mean narrow assumptions.',
          'When distributions are skewed, averages can mislead.',
          'Decisions need a loss function, not only the highest-probability event.'
        ],
        outcome: 'The useful question is not just whether something happens, but under what conditions, at what cost, and with how much uncertainty.'
      },
      uncertainty: {
        code: 'RISK',
        title: 'Confidence comes from traceability, not confident tone',
        summary: 'A model can sound certain. What matters is support: input quality, graph coverage, agent diversity, number of sampled paths, tool evidence, and historical calibration.',
        steps: [
          'Identify uncertainty sources: text gaps, model assumptions, LLM randomness, and external shocks.',
          'Check whether report tools and data support the conclusion.',
          'Inspect whether branches converge or split.',
          'Turn high-risk conclusions into hypotheses that need verification.'
        ],
        checks: [
          'High confidence with low evidence density is a warning sign.',
          'If a few agents drive the result, check representativeness.',
          'Predictions about surprise events should stay conservative.',
          'Stating limits clearly is more valuable than a polished answer.'
        ],
        outcome: 'A trustworthy forecast is not uncertainty-free; it knows where uncertainty lives.'
      },
      report: {
        code: 'REPORT',
        title: 'Reports are inspectable reasoning artifacts',
        summary: 'The report stage assembles a ReACT process: outline first, then XAI tools over timelines, factions, metrics, beliefs, and evidence, then a shareable or exportable analysis.',
        steps: [
          'Report Orchestrator creates a section plan.',
          'Each section calls tools over the database and timeline.',
          'The LLM integrates evidence, charts, and limitations.',
          'Reports can export PDF and share through a token.'
        ],
        checks: [
          'Conclusions should trace back to simulation events or graph evidence.',
          'Do not accept strong causal claims without comparison branches.',
          'The report should separate observations, inferences, and recommendations.',
          'Before regenerating, make sure the simulation session has not been cleaned up.'
        ],
        outcome: 'A good report helps you ask sharper questions; it should not end thinking.'
      },
      interaction: {
        code: 'ASK',
        title: 'Use interaction to audit the model, not just chat',
        summary: 'Step 5 can interview agents, question the Narrative Analyst, inspect memory behind an action, and propose what-if assumptions to see whether positions change.',
        steps: [
          'Choose the report analyst or a specific agent.',
          'Ask about a round, faction, metric, action, or causal chain.',
          'Ask agents to reference their memories and belief changes.',
          'Inject hypothetical shocks and compare answer consistency.'
        ],
        checks: [
          'Make questions specific: round, metric, actor, and action.',
          'An agent answer is in-character reasoning, not ground truth.',
          'If an answer conflicts with the report, inspect the timeline and database evidence.',
          'Use interaction to find risks, not only supporting quotes.'
        ],
        outcome: 'Treat interaction as an audit surface. “How do you know?” is usually more valuable than “What do you think?”'
      },
      limits: {
        code: 'LIMITS',
        title: 'Model boundaries belong before decisions',
        summary: 'Murmura is shaped by seed text, LLM provider, data lag, simulation preset, OASIS runtime, and cost caps. Knowing the boundary tells you where the result can and cannot be used.',
        steps: [
          'Check that seed text contains enough background and time horizon.',
          'Confirm step-specific models and API keys in Settings are usable.',
          'Review cost, concurrency, agent count, and rounds for the use case.',
          'Label which data is live, delayed, simulated, or LLM-inferred.'
        ],
        checks: [
          'Do not use demo-mode results for high-risk decisions.',
          'Legal, medical, financial, and safety use cases need external expert review.',
          'Prompt-injection-bearing inputs must pass safety sanitization.',
          'Old sessions may not reflect latest data or model settings.'
        ],
        outcome: 'The professional use of Murmura is stress-testing a decision process, not replacing the decision-maker.'
      }
    },
    glossary: [
      { term: 'Seed Text', desc: 'The raw scenario, document, or question context you provide to the system.' },
      { term: 'Knowledge Firewall', desc: 'Prompt constraints that force reasoning from the seed text instead of later knowledge.' },
      { term: 'Tipping Point', desc: 'A critical moment where the system distribution shifts or branches sharply.' },
      { term: 'p10-p90', desc: 'The band containing 80% of sampled outcomes, useful for tail risk and uncertainty.' },
      { term: 'Stakeholder', desc: 'An actor who can affect the result or is materially affected by it.' },
      { term: 'What-If Fork', desc: 'A new timeline created by injecting a shock at a round for counterfactual comparison.' }
    ]
  },
  workspace: {
    title: 'Workspace',
    subtitle: 'All prediction simulation sessions',
    adminBtn: 'Performance',
    newBtn: '+ New Prediction',
    loading: 'Loading sessions...',
    retry: 'Retry',
    empty: {
      title: 'No Predictions Yet',
      description: 'Create your first social simulation'
    },
    status: {
      completed: 'Completed',
      running: 'Running',
      failed: 'Failed',
      pending: 'Pending',
      created: 'Created'
    },
    meta: {
      agents: 'agents',
      rounds: 'rounds'
    },
    evidence: 'Evidence Search',
    loadMore: 'Load More'
  },
  home: {
    eyebrow: 'Universal Prediction Workbench',
    subtitle: 'Universal Prediction Engine',
    description: 'Drop any seed text — news, fiction, geopolitical events — AI auto-builds the world, spawns agents, and starts simulation. Combines Multi-Agent Systems, Knowledge Graphs, and Macro Forecasting to foresee collective behavior.',
    consoleTitle: 'Prediction Console',
    consoleStatus: 'System Status',
    consoleStatusLive: 'Available',
    consoleSignal: 'Clean-room UI · 5-step workflow',
    pipelineTitle: '5-Step Control Flow',
    examplesTitle: 'Example Scenarios',
    sampleWar: 'Energy-market reaction after geopolitical escalation',
    sampleFiction: 'Collective choices across factions in a fictional world',
    sampleCompany: 'B2B supply-chain reaction after a new competitor enters',
    inputLabel: 'INPUT',
    fileLabel: 'SEED FILE',
    seedLabel: 'SEED TEXT',
    questionLabel: 'QUESTION',
    presetLabel: 'RUN PRESET',
    toolsTitle: 'Engineering Tools',
    domainPacks: 'domain packs',
    metrics: {
      zeroConfig: 'Zero Config',
      kg: 'GraphRAG',
      oasis: 'OASIS',
      react: 'ReACT'
    },
    workflow: {
      graph: 'Extract entities, relations, and hidden stakeholders',
      env: 'Generate agents, platform identities, and scenario config',
      sim: 'Run multi-agent simulation and emergence hooks',
      report: 'Generate traceable reports through XAI tools',
      interact: 'Interview agents and explore What-If branches'
    },
    startTitle: 'Start Predicting Now',
    startSubtitle: 'Upload a document or enter seed text, AI handles the rest',
    dropLabel: 'Drop file here, or click to browse',
    dropHint: 'Supports PDF, TXT, Markdown · Max 10 MB',
    or: 'OR',
    textareaPlaceholder: 'Enter scenario description, e.g. Fed announces 200bps rate hike, global markets panic sell...',
    questionPlaceholder: '(Optional) What do you want to predict? e.g. Which faction will dominate? How will social sentiment evolve?',
    launchBtn: 'One-Click Predict',
    launching: 'Launching...',
    realitySeed: {
      label: 'Reality Seed',
      title: 'Generate Reality Seed',
      latest: 'Fetch latest',
      topic: 'TOPIC',
      topicPlaceholder: 'e.g. Iran-US war risk, Wuhan University public opinion, a company rivalry',
      requirement: 'SIMULATION REQUIREMENT',
      requirementPlaceholder: 'What do you want to simulate? e.g. If the US intervenes directly, how will public opinion and energy markets react?',
      attach: 'Attach material',
      clear: 'Remove',
      generate: 'Generate Seed PDF',
      generating: 'Generating...',
      ready: 'Seed dossier generated with {count} sources; its seed text is now inserted below.',
      openPdf: 'Open PDF',
      error: 'Failed to generate reality seed'
    },
    customDomain: 'Custom Domain Pack',
    dataConnector: 'Data Connector',
    godView: 'God View',
    presets: {
      fast: 'Fast',
      fastHint: '100 agents · 15 rounds (~2 min)',
      standard: 'Standard',
      standardHint: '300 agents · 20 rounds (~8 min)',
      deep: 'Deep',
      deepHint: '500 agents · 30 rounds (~20 min)'
    },
    errors: {
      format: 'Support for {ext} format is not available. Please upload PDF, TXT, or Markdown.',
      size: 'File size exceeds unique 10 MB limit.',
      launch: 'Launch failed, please try again.'
    }
  },
  onboarding: {
    skip: 'Skip',
    next: 'Next',
    finish: 'Finish',
    steps: {
      scenario: { title: 'Select Scenario', desc: 'Choose a social issue from the home page as the starting point.' },
      graph: { title: 'Knowledge Graph', desc: 'The system automatically builds a KG to show causal relationships.' },
      simulation: { title: 'Run Simulation', desc: 'Observe how AI agents interact, decide, and form trends.' }
    }
  },
  landing: {
    nav: {
      howItWorks: 'How it works',
      features: 'Features',
      launch: 'Launch Engine →'
    },
    hero: {
      eyebrow: 'UNIVERSAL PREDICTION ENGINE',
      title: 'Drop any text.',
      titleAccent: 'Simulate any world.',
      sub: 'Feed Murmura a sentence, a document, or a scenario — it builds the knowledge graph, spawns agents, runs the simulation, and predicts collective outcomes.',
      cta: 'Start Predicting',
      workspace: 'Workspace',
      stats: {
        agents: 'Agents per run',
        macro: 'Macro indicators',
        monteCarlo: 'Monte Carlo trials',
        xai: 'XAI analysis tools'
      }
    },
    workflow: {
      label: 'HOW IT WORKS',
      title: '5-Step Workflow',
      steps: {
        graph: { label: 'GRAPH', title: 'Knowledge Graph', desc: 'Seed text → entity extraction → causal network auto-built' },
        env: { label: 'ENV', title: 'Environment Setup', desc: 'Agent factory generates profiles from KG nodes, zero config needed' },
        sim: { label: 'SIM', title: 'Simulation', desc: 'OASIS multi-agent engine runs with emergent behavior fully on' },
        report: { label: 'REPORT', title: 'ReACT Report', desc: '3-phase LLM: outline → per-section tool calls → markdown assembly' },
        interact: { label: 'INTERACT', title: 'Deep Interaction', desc: 'Interview agents, inject shocks, branch into What-If scenarios' }
      }
    },
    features: {
      label: 'CAPABILITIES',
      title: 'What the Engine Does',
      list: {
        universal: { title: 'Universal Mode', desc: 'Drop any seed text — news, fiction, geopolitics. Engine infers actors, decisions, metrics, shocks automatically.' },
        kg: { title: 'Knowledge Graph', desc: 'GraphRAG tracks entity relationships and causal chains. Snapshots every 5 rounds, evolves with each interaction.' },
        emergence: { title: 'Emergence Engine', desc: 'Faction formation, tipping points, echo chambers, virality cascades — all emergent, not scripted.' },
        monteCarlo: { title: 'Monte Carlo', desc: '100-trial LHS + t-Copula sampling. Wilson score confidence intervals. Up to 10,000 stochastic trials.' },
        macro: { title: 'Macro Feedback', desc: '11 macro indicators updated per round. Agent micro-decisions feed back into macro state in real time.' },
        scenarios: { title: 'Scenario Branches', desc: 'Fork any simulation at any round. Compare diverging timelines side by side.' }
      }
    },
    useCases: {
      label: 'USE CASES',
      title: 'Works on Any Domain',
      list: {
        geopolitics: { tag: 'Geopolitics', desc: 'Taiwan Strait escalation, Iran-Israel scenarios, trade war cascades' },
        finance: { tag: 'Finance', desc: 'Fed rate hike contagion, crypto market panics, corporate competition' },
        society: { tag: 'Society', desc: 'Policy impact modeling, social movement dynamics, demographic shifts' },
        fiction: { tag: 'Fiction', desc: 'Dream of the Red Chamber, Harry Potter, any narrative world' }
      }
    },
    cta: {
      label: 'READY TO SIMULATE?',
      title: 'Drop your first scenario',
      sub: 'No configuration needed. Paste any text and the engine handles the rest.',
      btn: 'Launch Engine →'
    },
    footer: {
      desc: 'Universal Prediction Engine · Agent-Based Simulation',
      copy: 'Built with FastAPI · Vue 3 · OASIS · LanceDB'
    }
  },
  workflowGraph: {
    kicker: 'LIVE WORKFLOW',
    title: 'Dynamic Agent Graph',
    queued: 'queued',
    seed: 'SEED',
    graph: 'GRAPH',
    agents: 'AGENTS',
    sim: 'SIM',
    report: 'REPORT',
    nodes: 'NODES',
    edges: 'EDGES',
    agentCount: 'AGENTS',
    agent: 'Agent',
    waiting: 'Waiting for workflow events...'
  },
  process: {
    nav: {
      steps: {
        graph: { label: 'Graph Build', navLabel: 'GRAPH' },
        env: { label: 'Env Setup', navLabel: 'ENV' },
        sim: { label: 'Simulation', navLabel: 'SIM' },
        report: { label: 'Report Gen', navLabel: 'REPORT' },
        interact: { label: 'Interaction', navLabel: 'INTERACT' }
      },
      expressBadge: '⚡ Express Mode · Auto-configured'
    },
    workbench: {
      subtitle: 'A five-step prediction pipeline from seed text to traceable report',
      step: 'STEP',
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
    views: {
      label: 'Workflow View',
      evidence: 'Evidence',
      split: 'Split',
      workbench: 'Workbench'
    },
    context: {
      label: 'Workflow Context',
      expectedOutput: 'Expected Output',
      pipeline: 'Pipeline',
      metrics: {
        session: 'SESSION',
        graph: 'GRAPH',
        mode: 'MODE'
      },
      steps: {
        graph: {
          title: 'Turn the world into a graph first',
          desc: 'Handle seed text, documents, and persona data here, extracting entities, relationships, and hidden stakeholders for the simulation to reference.',
          output: 'Knowledge graph, node/edge statistics, scenario type, and usable graph id.'
        },
        env: {
          title: 'Convert the graph into a runnable environment',
          desc: 'Generate agents, platform identities, round counts, shock schedules, and macro scenarios. Beginner mode stays compact; advanced mode exposes deeper controls.',
          output: 'Simulation session, agent configuration, platform setup, and shock schedule.'
        },
        sim: {
          title: 'Observe the current simulation only',
          desc: 'Run the OASIS multi-agent simulation while tracking rounds, actions, beliefs, factions, shocks, and emergence hooks. This step should feel like monitoring an experiment.',
          output: 'Timeline, agent actions, emergence metrics, and completion state.'
        },
        report: {
          title: 'Generate a traceable report',
          desc: 'Use the ReACT report flow to turn simulation data into conclusions while preserving tool calls, evidence tags, and the XAI sidebar.',
          output: 'Report id, Markdown report, PDF/share entry points, and clickable evidence.'
        },
        interact: {
          title: 'Enter deep interaction',
          desc: 'Use the completed report and simulation memory to interview agents, inspect dossiers, and explore What-If branches.',
          output: 'Agent interviews, memory search, roleplay dialogue, and follow-up branches.'
        }
      }
    },
    errors: {
      graphFirst: 'Please complete Graph Build first',
      envFirst: 'Please complete Env Setup and start simulation',
      simFirst: 'Report can be generated after simulation completes',
      reportFirst: 'Please generate report first',
      engineUnavailable: 'Simulation engine unavailable — use Docker for full features',
      engineUnavailableDetail: 'Simulation engine unavailable — use Docker for full features. The workflow will stop after Environment Setup.',
      workflowPolling: 'Workflow polling failed'
    }
  },
  step2: {
    badges: {
      experimental: 'Experimental'
    },
    actions: {
      creating: 'Creating...',
      start: 'Start Simulation'
    }
  },
  settings: {
    header: {
      title: 'Settings',
      subtitle: 'Manage API keys, model selection, and system preferences'
    },
    tabs: {
      navLabel: 'Settings sections',
      api: {
        title: 'API Keys',
        desc: 'Configure API keys for LLM providers. Keys are stored encrypted and masked upon display.',
        empty: '— Not Set —',
        testing: '⏳ Testing...',
        test: 'Test',
        save: 'Save',
        verifying: '⏳ Verifying key...',
        connFailed: 'Connection failed',
        show: 'SHOW',
        hide: 'HIDE',
        showKey: 'Show key',
        hideKey: 'Hide key',
        keyInputAria: '{provider} API key',
        testKeyAria: 'Test {provider} key',
        saveKeyAria: 'Save {provider} key'
      },
      model: {
        title: 'Model Selection',
        desc: 'Choose one primary LLM for the whole workflow. Per-step routing is only needed for cost or quality tuning.',
        quickApply: 'Quick apply:',
        advanced: 'Advanced: per-step overrides',
        globalFallback: 'Global Defaults (used when no per-step model is set)',
        provider: 'Provider',
        model: 'Model',
        simple: {
          eyebrow: 'Simple routing',
          title: 'One model for the full simulation flow',
          desc: 'Reality Seed, graph build, simulation agents, and report generation will share this model. Saving clears old per-step overrides so one stale provider or invalid model id cannot break a step.',
          recommended: 'Use recommended',
          save: 'Apply to workflow',
          saving: 'Saving model routing...',
          saved: 'Applied; the full workflow now uses this model',
          fillBoth: 'Choose a provider and enter a model',
          routingSeed: 'Reality Seed',
          routingSimulation: 'Simulation',
          routingReport: 'Report',
          sameModel: 'Same model'
        },
        models: {
          sync: 'Sync models',
          syncing: 'Syncing...',
          chooseProvider: 'Choose a provider first',
          unsupported: 'This provider does not support automatic model discovery yet; enter a model id manually',
          notLoaded: 'Model list has not been synced yet; save/test an API key or sync models',
          loading: 'Loading model list...',
          loaded: '{count} models loaded; you can still enter an unlisted model id manually'
        },
        steps: {
          useGlobal: 'Use global default',
          fillBoth: 'Please fill in both Provider and Model',
          step1: { label: 'Step 1: Knowledge Graph Build', hint: 'Recommend a fast model (e.g. deepseek-v3); called frequently during entity extraction' },
          step2: { label: 'Step 2: Environment Setup', hint: 'Recommend a strong reasoning model for agent profile generation and scenario analysis' },
          step3: { label: 'Step 3: Simulation Run', hint: 'Main model for key stakeholders; Lite model for background agents (saves cost)' },
          step4: { label: 'Step 4: Report Generation', hint: 'Recommend a long-form capable model (e.g. Gemini Pro, GPT-4o)' },
          step5: { label: 'Step 5: Interaction', hint: 'Recommend a conversational model for Interview Engine' },
        },
        agent: {
          title: 'Agent Decision LLM (Global)',
          providerHint: 'Provider used for agent thinking, decision-making, and interactions',
          main: 'Agent Model (Main)',
          mainHint: 'Stakeholder agents use this model',
          lite: 'Agent Model (Lite)',
          liteHint: 'Background agents use this cheaper model (optional)'
        },
        report: {
          title: 'Report Generation LLM (Global)',
          providerHint: 'LLM used for final reports, summaries, and chart analysis',
          model: 'Report Model',
          modelHint: 'Leave blank to use the provider\'s default model'
        }
      },
      sim: {
        title: 'Simulation Defaults',
        desc: 'Set default parameters for new simulations.',
        preset: 'Default Preset',
        agents: 'Default Agent Count',
        agentsUnit: 'agents',
        agentsHint: 'Default number of agents when creating a new simulation (5–500)',
        concurrency: 'Concurrency Limit',
        concurrencyHint: 'Max concurrent LLM requests. Recommended: 30–80',
        domain: 'Default Domain Pack',
        domainHint: 'Default Domain Pack ID applied to new simulations'
      },
      ui: {
        title: 'UI Preferences',
        desc: 'The following preferences are saved locally (localStorage) and apply immediately.',
        lang: 'UI Language',
        itemsPerPage: 'Items Per Page',
        autoOpen: 'Auto-open report after simulation',
        autoOpenHint: 'Automatically navigate to the Report page when simulation completes'
      },
      data: {
        title: 'Data Sources',
        desc: 'Configure external data source API keys and integration options.',
        empty: '— Not Set —',
        test: 'Test',
        save: 'Save',
        verifying: '⏳ Verifying...',
        ref: 'From',
        fred: 'FRED API Key',
        fredHint: 'From <a href="https://fred.stlouisfed.org/docs/api/api_key.html" target="_blank" rel="noopener">St. Louis Fed</a>, used for fetching macroeconomic data',
        externalFeed: 'Enable External Feeds',
        externalFeedHint: 'When enabled, the system periodically updates data from FRED, World Bank, etc.',
        refreshInterval: 'Refresh Interval',
        seconds: 'seconds',
        refreshHint: 'Interval between automatic updates (300–86400 seconds)'
      }
    }
  }
}
