"""
Centralized translation dictionary for Arabic/English UI
"""

UI_TEXT = {
    'ar': {
        # Page config
        'page_title': 'نظام شات بوت للرعاية الصحية مبني على التقنيات الذكية',
        'page_subtitle': 'Healthcare Chatbot System Based on Intelligent Techniques',
        'header_title': 'نظام شات بوت للرعاية الصحية مبني على التقنيات الذكية',

        # Sidebar - Control Panel
        'control_panel': 'لوحة التحكم',
        'new_session': 'بدء جلسة جديدة',
        'current_session': 'الجلسة الحالية',
        'facts_collected': 'الحقائق المجموعة',
        'risk_level': 'مستوى الخطر',
        'confidence': 'الثقة',

        # Sidebar - Dashboard
        'dashboard': 'لوحة المعلومات',
        'no_facts': 'لم يتم جمع حقائق بعد',
        'not_assessed': 'لم يتم التقييم بعد',

        # Sidebar - Examples
        'writing_examples': 'أمثلة على طرق الكتابة',

        # Sidebar - Previous Sessions
        'previous_sessions': 'الجلسات السابقة',
        'load': 'تحميل',
        'delete': 'حذف',
        'loaded': 'تم التحميل!',
        'no_sessions': 'لا توجد جلسات محفوظة',
        'date': 'التاريخ',
        'facts': 'الحقائق',

        # Sidebar - Language
        'language': 'اللغة',
        'choose_language': 'اختر اللغة',

        # Main area - No session
        'start_session_prompt': 'الرجاء بدء جلسة جديدة من الشريط الجانبي',
        'smart_system_title': 'نظام ذكي',
        'smart_system_items': ['حوار ذاتي داخلي', 'استنتاج تلقائي', 'أولويات ديناميكية'],
        'safe_storage_title': 'تخزين آمن',
        'safe_storage_items': ['حفظ جميع الخطوات', 'تتبع كامل للحقائق', 'استرجاع الجلسات'],
        'accurate_analysis_title': 'تحليل دقيق',
        'accurate_analysis_items': ['تقييم مستوى الخطر', 'تحذيرات فورية', 'تقارير شاملة'],

        # Main area - Dialog
        'dialog_area': 'منطقة الحوار',
        'tell_health': 'أخبرني عن حالتك الصحية',
        'next_question_label': 'السؤال التالي',
        'write_info': 'اكتب معلوماتك هنا:',
        'write_placeholder': 'مثال: عمري 67 سنة، ذكر، الطول 175 والوزن 98، مدخّن حالي، أعمل بمصنع، عندي ضغط وسكري وأمراض قلب وأمراض مزمنة، السكر التراكمي 8 والكوليسترول 280، ويوجد تاريخ عائلي...',
        'write_help': 'اكتب بأي طريقة تريد - بالعربية أو الإنجليزية',
        'analyze_send': 'تحليل وإرسال',
        'clear': 'مسح',

        # Progress
        'progress': 'التقدم',
        'progress_text': 'تم جمع {done} من {total} حقيقة ({pct}%)',
        'remaining_fields': 'الحقول المتبقية',
        'completed_fields': 'الحقول المُكتملة',
        'field': 'حقل',
        'remaining': 'المتبقية',
        'can_write': 'يمكنك كتابة أي منها أو كلها في حقل الإدخال بالأسفل',

        # Processing results
        'great_processed': 'رائع! تم فهم ومعالجة **{count}** معلومة بنجاح!',
        'info_understood': 'المعلومات التي فهمتها منك:',
        'could_not_understand': 'لم أتمكن من فهم بعض الأجزاء: {parts}',
        'info_saved': 'تم حفظ المعلومات بنجاح!',
        'write_first': 'الرجاء كتابة معلوماتك أولاً',
        'all_collected': 'تم جمع جميع الحقائق!',
        'continue_next': 'متابعة للسؤال التالي',
        'transitioning': 'جاري الانتقال للسؤال التالي...',
        'could_not_extract': 'لم أتمكن من استخراج معلومات واضحة من النص.',
        'tips_title': 'نصائح للحصول على نتائج أفضل:',
        'tip1': 'استخدم أرقام واضحة (مثل: 55، 140/90)',
        'tip2': 'اذكر الكلمات المفتاحية (عمر، ضغط، كوليسترول، ألم)',
        'tip3': 'يمكنك الكتابة بالعربية أو الإنجليزية',
        'tip4': 'جرب صياغة مختلفة للجمل',
        'attempt_counter': '⚠️ محاولة {n}/{max} — {purpose}',
        'attempt_purpose_example': 'مع مثال',
        'attempt_purpose_last': 'آخر محاولة + تحذير',
        'auto_skipped': '⏭️ تم تخطّي السؤال تلقائياً بعد {max} محاولات. تم تسجيل القيمة الطبيعية الافتراضية ({value}) — يستطيع الطبيب مراجعتها لاحقاً.',
        'skipped_badge': 'مُتخطى',

        # Assessment
        'comprehensive_assessment': 'التقييم الشامل - Comprehensive Assessment',
        'section1_domain': 'القسم الأول: تحليل القواعد الطبية',
        'section1_subtitle': 'Domain Rules Analysis',
        'risk_level_label': 'مستوى الخطر',
        'rules_applied': 'القواعد المُطبقة',
        'risk_factors': 'عوامل الخطر',
        'recommendations': 'التوصيات',

        'section2_features': 'القسم الثاني: الخصائص المتقدمة',
        'section2_subtitle': 'Advanced Features Summary',
        'classification': 'التصنيف:',
        'age': 'العمر',
        'cholesterol': 'الكوليسترول',
        'blood_pressure': 'ضغط الدم',
        'physical_capacity': 'القدرة البدنية:',
        'capacity': 'القدرة',
        'total_features': 'إجمالي الخصائص المولدة:',

        'section3_ml': 'القسم الثالث: تنبؤ نموذج التعلم الآلي',
        'section3_subtitle': 'ML Model Prediction',
        'prediction': 'التنبؤ',
        'positive': 'إيجابي',
        'negative': 'سلبي',
        'probability': 'الاحتمالية',
        'source': 'المصدر',

        'section4_decision': 'القسم الرابع: القرار النهائي الشامل',
        'section4_subtitle': 'Final Comprehensive Decision',
        'final_decision': 'القرار النهائي',
        'reasoning': 'التفسير',
        'decision_sources': 'مصادر القرار',
        'medical_rules': 'القواعد الطبية:',
        'ml_model': 'نموذج ML:',
        'applied_rules': 'القواعد المطبقة',
        'final_recommendations': 'التوصيات النهائية',

        'decision_tree_title': 'Rule-Based Decision Tree Visualization',
        'decision_tree_subtitle': 'رسم شجرة القرار - Graphviz Style',
        'tab_tree': 'Decision Tree Diagram',
        'tab_rules': 'Decision Rules Table',
        'tab_flow': 'Process Flow',

        'show_full_json': 'عرض التقييم الكامل (JSON)',
        'show_legacy': 'عرض التقرير النهائي (Legacy)',

        # Step-by-step demo tabs (after 11 fields collected)
        'tab_old_way': 'الطريقة القديمة',
        'tab_step_by_step': 'خطوة خطوة',
        'demo_start_button': 'ابدأ العرض التفاعلي',
        'demo_start_intro': 'سنعرض رحلة التشخيص في 7 مراحل — كل مرحلة تشرح ما يحدث بلغة مبسّطة. اضغطي "ابدأ" متى تكونين جاهزة.',
        'demo_progress': 'المرحلة {n} من {total}',
        'demo_prev': 'السابق',
        'demo_next': 'التالي',
        'demo_restart': 'إعادة من البداية',
        'demo_finish': 'انتهى العرض — تم!',
        'demo_what_happens': 'ماذا يحدث الآن؟',

        # Step 1 — Raw input
        'demo_s1_title': 'المرحلة 1: البيانات الخام للمريض',
        'demo_s1_explain': 'هذه هي الـ 9 معلومات الأصل التي جمعناها من المريض. النظام سيستخدمها أساساً لكل القرارات التالية.',
        'demo_s1_table_field': 'الحقل',
        'demo_s1_table_value': 'القيمة',
        'demo_s1_table_source': 'المصدر',

        # Step 2 — Feature Engineering
        'demo_s2_title': 'المرحلة 2: هندسة الخصائص',
        'demo_s2_explain': 'حوّلنا حقولك إلى 18 ميزة سريرية يستهلكها النموذج — مثل: العمر، مؤشر كتلة الجسم، حالة التدخين المُرمّزة، الضغط والسكري وأمراض القلب، والسكر التراكمي والكوليسترول...',
        'demo_s2_count_label': 'إجمالي المؤشّرات المُولّدة',
        'demo_s2_examples_label': 'أمثلة على المؤشّرات المتقدّمة:',

        # Step 3 — Domain Rules
        'demo_s3_title': 'المرحلة 3: القواعد الطبية',
        'demo_s3_explain': 'النظام يحتوي على 48 قاعدة طبية معتمدة من جمعية القلب الأمريكية (ACC/AHA). فحصناها كلها — وهذه القواعد التي تنطبق على المريض:',
        'demo_s3_triggered_label': 'القواعد المُفعّلة',
        'demo_s3_total_label': 'إجمالي القواعد المتاحة',

        # Step 4 — ERPM
        'demo_s4_title': 'المرحلة 4: الشبكة العصبية ERPM',
        'demo_s4_explain': 'استخدمنا نموذج تعلّم آلي بـ 79,809 معامل تم تدريبه على آلاف الحالات الحقيقية. أعطى احتمالية إصابة المريض كرقم بين 0% و 100%.',
        'demo_s4_prediction_label': 'تنبؤ النموذج',
        'demo_s4_probability_label': 'احتمالية الإصابة',
        'demo_s4_params_note': 'النموذج: ERPM • 79,809 معامل • 21 طبقة',

        # Step 5 — Decision Fusion
        'demo_s5_title': 'المرحلة 5: دمج القرارات',
        'demo_s5_explain': 'لا نعتمد على مصدر واحد — جمعنا حكمة الأطباء (القواعد الطبية) مع قوة الحاسوب (الشبكة العصبية) للحصول على قرار متوازن وأكثر دقّة.',
        'demo_s5_domain_label': 'رأي القواعد الطبية',
        'demo_s5_ml_label': 'رأي الشبكة العصبية',
        'demo_s5_fusion_label': 'القرار المُدمج',
        'demo_s5_how_label': 'كيف تم دمج القرارين؟',
        'demo_s5_how_intro': 'يستخدم النظام شجرة قرار من 10 قواعد ذات أولوية تفحص نتيجة القواعد الطبية ونتيجة الشبكة العصبية معاً — وأوّل قاعدة تنطبق هي التي تُحدّد القرار النهائي.',
        'demo_s5_rule_fired': 'القاعدة المُطبَّقة على هذه الحالة:',
        'demo_s5_confidence_label': 'ثقة القرار',
        'demo_s5_tree_label': 'جدول القواعد الـ 10 (القاعدة المُطبَّقة مُمَيَّزة):',
        'demo_s5_table_num': '#',
        'demo_s5_table_condition': 'الشرط',
        'demo_s5_table_output': 'المخرج',
        'demo_s5_table_status': 'الحالة',
        'demo_s5_applied': 'تطبّقت',
        'demo_s5_not_applied': '—',

        # Step 6 — Risk Stratification
        'demo_s6_title': 'المرحلة 6: تصنيف مستوى الخطر',
        'demo_s6_explain': 'صنّفنا المريض وفق معايير جمعية القلب الأمريكية ACC/AHA 2019: منخفض (<5%) / حدّي (5-7.5%) / متوسط (7.5-20%) / عالي (>20%).',
        'demo_s6_final_label': 'تصنيف المريض',

        # Step 7 — Final Decision + Recommendations
        'demo_s7_title': 'المرحلة 7: القرار النهائي والتوصيات',
        'demo_s7_explain': 'هذا هو ملخّص كل ما سبق — مع التوصيات الطبية للمريض. يمكن تحميل التقرير الكامل كـ PDF أسفل الصفحة.',
        'demo_s7_final_decision_label': 'القرار النهائي',
        'demo_s7_recommendations_label': 'التوصيات الطبية',

        # Conversation display
        'first_question': 'السؤال الأول',
        'basic_question': 'سؤال أساسي',
        'first_q_note': 'هذا السؤال الأساسي الذي يبدأ به التشخيص دائماً',
        'answer_examples': 'أمثلة على الإجابة',
        'note': 'ملاحظة:',
        'you': 'أنت',
        'analysis': 'التحليل',
        'inference': 'الاستنتاج',
        'decision_label': 'القرار',
        'important_warning': 'تحذير مهم',
        'why_important': 'لماذا هذا السؤال مهم؟',
        'next_important_q': 'السؤال التالي الأهم',
        'smart_system': 'النظام الذكي',
        'priority_critical': 'عالية جداً',
        'priority_high': 'عالية',
        'priority_medium': 'متوسطة',
        'priority_normal': 'عادية',

        # Conversation & Facts table
        'conversation': 'المحادثة',
        'col_field': 'الحقل',
        'col_value': 'القيمة',
        'col_time': 'الوقت',

        # Groq AI (v7.0.0)
        'groq_settings': 'إعدادات الذكاء الاصطناعي',
        'groq_api_key': 'مفتاح Groq API',
        'groq_help': 'أدخل مفتاح Groq API للحصول على تفسير ذكي وتوصيات مخصصة',
        'groq_connected': 'تم الاتصال بـ Groq AI بنجاح!',
        'groq_error': 'فشل الاتصال بـ Groq API. تحقق من المفتاح.',
        'groq_optional': 'اختياري — النظام يعمل بدونه',
        'groq_not_connected': 'أدخل مفتاح Groq API في الشريط الجانبي للحصول على تفسير ذكي وتوصيات مخصصة بالذكاء الاصطناعي.',
        'section5_groq': 'القسم 5: تحليل الذكاء الاصطناعي',
        'section5_subtitle': 'تفسير النتائج وتوصيات مخصصة باستخدام Groq AI',
        'ai_interpretation': 'تفسير الذكاء الاصطناعي',
        'personalized_recommendations': 'توصيات مخصصة لحالتك',
        'powered_by_groq': 'مدعوم بـ Groq AI (llama-3.3-70b-versatile)',

        # Smart Conversation (v8.0.0)
        'smart_mode_active': 'الوضع الذكي مفعّل',
        'smart_mode_badge': 'محادثة ذكية',
        'classic_mode_badge': 'الوضع الكلاسيكي',
        'doctor_label': 'الطبيب',
        'patient_label': 'المريض',
        'smart_extracting': 'جاري تحليل إجابتك...',
        'fields_extracted': 'تم استخراج {count} معلومة',
        'smart_fallback_notice': 'تم التبديل للوضع الكلاسيكي مؤقتاً',
        'type_your_message': 'اكتب رسالتك هنا...',
        'send_message': 'إرسال',
        'smart_greeting_default': 'مرحباً بك! أخبرني عن نفسك وعن أي شكوى تعاني منها.',
        'ack_understand': 'أفهم، شكراً لك على المعلومة.',
        'ack_with_field': 'أفهم، تم تسجيل {label}: {value}.',
        'ack_next_question_prefix': 'الآن سؤالي التالي:',
        'all_fields_collected': 'تم جمع جميع المعلومات المطلوبة! جاري تحضير التقييم...',
        'extracted_info_label': 'المعلومات المستخرجة',

        # Voice Input / Output
        'voice_btn': 'سجل رسالتك الصوتية',
        'voice_recording': 'جاري تحويل الصوت إلى نص...',
        'voice_stopped': 'تم إيقاف التسجيل',
        'voice_not_supported': 'تعذر تحويل الصوت إلى نص',
        'listen_btn': 'استماع',
        'listening_now': 'جاري القراءة...',

        # Footer
        'footer_text': 'نظام الحوار الطبي الذكي | Medical Intelligent Dialog System',
        'footer_powered': 'Powered by Self-Reasoning AI + Groq AI • Made with ',

        # Risk gauge
        'risk_gauge_title': 'مستوى الخطر',

        # Session messages
        'session_started': 'تم بدء جلسة جديدة: {sid}',
        'start_session_first': 'الرجاء بدء جلسة جديدة أولاً!',

        # Field names
        'field_names': {
            'age': 'العمر',
            'gender': 'الجنس',
            'height_cm': 'الطول (سم)',
            'weight_kg': 'الوزن (كغم)',
            'bmi': 'مؤشر كتلة الجسم',
            'smoking_status': 'حالة التدخين',
            'years_smoked': 'سنوات التدخين',
            'years_since_quit': 'سنوات منذ الإقلاع',
            'workplace_type': 'نوع مكان العمل',
            'family_history': 'التاريخ العائلي',
            'hypertension': 'ارتفاع ضغط الدم',
            'diabetes': 'السكري',
            'cardiovascular_disease': 'أمراض القلب والأوعية',
            'chronic_diseases': 'أمراض مزمنة',
            'obesity': 'السمنة',
            'gestational_diabetes': 'سكري الحمل',
            'hba1c': 'السكر التراكمي',
            'cholesterol': 'الكوليسترول',
        },
    },

    'en': {
        # Page config
        'page_title': 'Healthcare Chatbot System Based on Intelligent Techniques',
        'page_subtitle': 'Healthcare Chatbot System Based on Intelligent Techniques',
        'header_title': 'Healthcare Chatbot System Based on Intelligent Techniques',

        # Sidebar - Control Panel
        'control_panel': 'Control Panel',
        'new_session': 'Start New Session',
        'current_session': 'Current Session',
        'facts_collected': 'Facts Collected',
        'risk_level': 'Risk Level',
        'confidence': 'Confidence',

        # Sidebar - Dashboard
        'dashboard': 'Dashboard',
        'no_facts': 'No facts collected yet',
        'not_assessed': 'Not assessed yet',

        # Sidebar - Examples
        'writing_examples': 'Writing Examples',

        # Sidebar - Previous Sessions
        'previous_sessions': 'Previous Sessions',
        'load': 'Load',
        'delete': 'Delete',
        'loaded': 'Loaded!',
        'no_sessions': 'No saved sessions',
        'date': 'Date',
        'facts': 'Facts',

        # Sidebar - Language
        'language': 'Language',
        'choose_language': 'Choose Language',

        # Main area - No session
        'start_session_prompt': 'Please start a new session from the sidebar',
        'smart_system_title': 'Smart System',
        'smart_system_items': ['Internal self-dialog', 'Auto inference', 'Dynamic priorities'],
        'safe_storage_title': 'Secure Storage',
        'safe_storage_items': ['Save all steps', 'Full fact tracking', 'Session recovery'],
        'accurate_analysis_title': 'Accurate Analysis',
        'accurate_analysis_items': ['Risk level assessment', 'Instant warnings', 'Comprehensive reports'],

        # Main area - Dialog
        'dialog_area': 'Dialog Area',
        'tell_health': 'Tell me about your health',
        'next_question_label': 'Next Question',
        'write_info': 'Write your information here:',
        'write_placeholder': 'Example: I am 67, male, height 175 weight 98, current smoker, work in a factory, I have hypertension, diabetes, heart disease and chronic conditions, HbA1c 8, cholesterol 280, family history yes...',
        'write_help': 'Write in any way you want - in Arabic or English',
        'analyze_send': 'Analyze & Send',
        'clear': 'Clear',

        # Progress
        'progress': 'Progress',
        'progress_text': 'Collected {done} of {total} facts ({pct}%)',
        'remaining_fields': 'Remaining Fields',
        'completed_fields': 'Completed Fields',
        'field': 'field',
        'remaining': 'Remaining',
        'can_write': 'You can write any or all of them in the input field below',

        # Processing results
        'great_processed': 'Great! Successfully processed **{count}** piece(s) of information!',
        'info_understood': 'Information understood from you:',
        'could_not_understand': 'Could not understand some parts: {parts}',
        'info_saved': 'Information saved successfully!',
        'write_first': 'Please write your information first',
        'all_collected': 'All facts have been collected!',
        'continue_next': 'Continue to Next Question',
        'transitioning': 'Transitioning to next question...',
        'could_not_extract': 'Could not extract clear information from the text.',
        'tips_title': 'Tips for better results:',
        'attempt_counter': '⚠️ Attempt {n}/{max} — {purpose}',
        'attempt_purpose_example': 'with example',
        'attempt_purpose_last': 'last try + warning',
        'auto_skipped': '⏭️ Skipped automatically after {max} attempts. Recorded the clinical default ({value}) so the doctor can review it later.',
        'skipped_badge': 'Skipped',
        'tip1': 'Use clear numbers (e.g.: 55, 140/90)',
        'tip2': 'Mention keywords (age, pressure, cholesterol, pain)',
        'tip3': 'You can write in Arabic or English',
        'tip4': 'Try different phrasing',

        # Assessment
        'comprehensive_assessment': 'Comprehensive Assessment',
        'section1_domain': 'Section 1: Medical Rules Analysis',
        'section1_subtitle': 'Domain Rules Analysis',
        'risk_level_label': 'Risk Level',
        'rules_applied': 'Rules Applied',
        'risk_factors': 'Risk Factors',
        'recommendations': 'Recommendations',

        'section2_features': 'Section 2: Advanced Features',
        'section2_subtitle': 'Advanced Features Summary',
        'classification': 'Classification:',
        'age': 'Age',
        'cholesterol': 'Cholesterol',
        'blood_pressure': 'Blood Pressure',
        'physical_capacity': 'Physical Capacity:',
        'capacity': 'Capacity',
        'total_features': 'Total generated features:',

        'section3_ml': 'Section 3: ML Model Prediction',
        'section3_subtitle': 'ML Model Prediction',
        'prediction': 'Prediction',
        'positive': 'Positive',
        'negative': 'Negative',
        'probability': 'Probability',
        'source': 'Source',

        'section4_decision': 'Section 4: Final Comprehensive Decision',
        'section4_subtitle': 'Final Comprehensive Decision',
        'final_decision': 'Final Decision',
        'reasoning': 'Reasoning',
        'decision_sources': 'Decision Sources',
        'medical_rules': 'Medical Rules:',
        'ml_model': 'ML Model:',
        'applied_rules': 'Applied Rules',
        'final_recommendations': 'Final Recommendations',

        'decision_tree_title': 'Rule-Based Decision Tree Visualization',
        'decision_tree_subtitle': 'Decision Tree Diagram - Graphviz Style',
        'tab_tree': 'Decision Tree Diagram',
        'tab_rules': 'Decision Rules Table',
        'tab_flow': 'Process Flow',

        'show_full_json': 'Show Full Assessment (JSON)',
        'show_legacy': 'Show Final Report (Legacy)',

        # Step-by-step demo tabs (after 11 fields collected)
        'tab_old_way': 'Classic View',
        'tab_step_by_step': 'Step-by-Step',
        'demo_start_button': 'Start Interactive Demo',
        'demo_start_intro': 'We will walk through the diagnostic journey in 7 stages — each stage explains what happens in plain language. Press "Start" when ready.',
        'demo_progress': 'Stage {n} of {total}',
        'demo_prev': 'Previous',
        'demo_next': 'Next',
        'demo_restart': 'Restart from beginning',
        'demo_finish': 'Demo complete — done!',
        'demo_what_happens': 'What happens now?',

        # Step 1 — Raw input
        'demo_s1_title': 'Stage 1: Raw Patient Data',
        'demo_s1_explain': 'These are the 9 base inputs we collected from the patient. The system will use them as the foundation for every decision that follows.',
        'demo_s1_table_field': 'Field',
        'demo_s1_table_value': 'Value',
        'demo_s1_table_source': 'Source',

        # Step 2 — Feature Engineering
        'demo_s2_title': 'Stage 2: Feature Engineering',
        'demo_s2_explain': 'We transformed your fields into 18 clinical features the model consumes — like age, BMI, encoded smoking status, hypertension/diabetes/heart disease, HbA1c and cholesterol.',
        'demo_s2_count_label': 'Total engineered indicators',
        'demo_s2_examples_label': 'Examples of advanced indicators:',

        # Step 3 — Domain Rules
        'demo_s3_title': 'Stage 3: Medical Rules',
        'demo_s3_explain': 'The system holds 48 medical rules grounded in ACC/AHA guidelines. We evaluated every one — these are the rules that fired for this patient:',
        'demo_s3_triggered_label': 'Rules triggered',
        'demo_s3_total_label': 'Total rules available',

        # Step 4 — ERPM
        'demo_s4_title': 'Stage 4: ERPM Neural Network',
        'demo_s4_explain': 'We used a machine-learning model with 79,809 parameters trained on thousands of real cases. It returns the patient\'s heart-disease probability as a number between 0% and 100%.',
        'demo_s4_prediction_label': 'Model prediction',
        'demo_s4_probability_label': 'Disease probability',
        'demo_s4_params_note': 'Model: ERPM • 79,809 parameters • 21 layers',

        # Step 5 — Decision Fusion
        'demo_s5_title': 'Stage 5: Decision Fusion',
        'demo_s5_explain': 'We do not rely on a single source — we combined clinical wisdom (medical rules) with computational power (neural network) for a balanced and more accurate decision.',
        'demo_s5_domain_label': 'Medical Rules verdict',
        'demo_s5_ml_label': 'Neural Network verdict',
        'demo_s5_fusion_label': 'Fused decision',
        'demo_s5_how_label': 'How were the two decisions fused?',
        'demo_s5_how_intro': 'The system uses a priority-ordered decision tree of 10 rules that look at the medical rules verdict and the neural network verdict together — the first rule that matches sets the final decision.',
        'demo_s5_rule_fired': 'Rule applied to this case:',
        'demo_s5_confidence_label': 'Decision confidence',
        'demo_s5_tree_label': 'The 10 fusion rules (the applied rule is highlighted):',
        'demo_s5_table_num': '#',
        'demo_s5_table_condition': 'Condition',
        'demo_s5_table_output': 'Output',
        'demo_s5_table_status': 'Status',
        'demo_s5_applied': 'Applied',
        'demo_s5_not_applied': '—',

        # Step 6 — Risk Stratification
        'demo_s6_title': 'Stage 6: Risk Stratification',
        'demo_s6_explain': 'We classified the patient per ACC/AHA 2019 standards: Low (<5%) / Borderline (5-7.5%) / Intermediate (7.5-20%) / High (>20%).',
        'demo_s6_final_label': 'Patient classification',

        # Step 7 — Final Decision + Recommendations
        'demo_s7_title': 'Stage 7: Final Decision and Recommendations',
        'demo_s7_explain': 'This is a summary of everything above — alongside the medical recommendations for the patient. The full PDF report is available below.',
        'demo_s7_final_decision_label': 'Final decision',
        'demo_s7_recommendations_label': 'Medical recommendations',

        # Conversation display
        'first_question': 'First Question',
        'basic_question': 'Basic Question',
        'first_q_note': 'This is the basic question that always starts the diagnosis',
        'answer_examples': 'Answer Examples',
        'note': 'Note:',
        'you': 'You',
        'analysis': 'Analysis',
        'inference': 'Inference',
        'decision_label': 'Decision',
        'important_warning': 'Important Warning',
        'why_important': 'Why is this question important?',
        'next_important_q': 'Most Important Next Question',
        'smart_system': 'Smart System',
        'priority_critical': 'Very High',
        'priority_high': 'High',
        'priority_medium': 'Medium',
        'priority_normal': 'Normal',

        # Conversation & Facts table
        'conversation': 'Conversation',
        'col_field': 'Field',
        'col_value': 'Value',
        'col_time': 'Time',

        # Groq AI (v7.0.0)
        'groq_settings': 'AI Settings',
        'groq_api_key': 'Groq API Key',
        'groq_help': 'Enter your Groq API key for AI-powered interpretation and personalized recommendations',
        'groq_connected': 'Connected to Groq AI successfully!',
        'groq_error': 'Failed to connect to Groq API. Check your key.',
        'groq_optional': 'Optional — system works without it',
        'groq_not_connected': 'Enter your Groq API key in the sidebar for AI-powered interpretation and personalized recommendations.',
        'section5_groq': 'Section 5: AI Analysis',
        'section5_subtitle': 'Result interpretation and personalized recommendations powered by Groq AI',
        'ai_interpretation': 'AI Interpretation',
        'personalized_recommendations': 'Personalized Recommendations',
        'powered_by_groq': 'Powered by Groq AI (llama-3.3-70b-versatile)',

        # Smart Conversation (v8.0.0)
        'smart_mode_active': 'Smart Mode Active',
        'smart_mode_badge': 'Smart Conversation',
        'classic_mode_badge': 'Classic Mode',
        'doctor_label': 'Doctor',
        'patient_label': 'Patient',
        'smart_extracting': 'Analyzing your response...',
        'fields_extracted': '{count} field(s) extracted',
        'smart_fallback_notice': 'Temporarily switched to classic mode',
        'type_your_message': 'Type your message here...',
        'send_message': 'Send',
        'smart_greeting_default': 'Welcome! Please tell me about yourself and any concerns you may have.',
        'ack_understand': 'I understand, thank you for sharing.',
        'ack_with_field': 'I understand — recorded {label}: {value}.',
        'ack_next_question_prefix': 'Now my next question is:',
        'all_fields_collected': 'All required information collected! Preparing assessment...',
        'extracted_info_label': 'Extracted Information',

        # Voice Input / Output
        'voice_btn': 'Record your voice message',
        'voice_recording': 'Converting speech to text...',
        'voice_stopped': 'Recording stopped',
        'voice_not_supported': 'Could not convert speech to text',
        'listen_btn': 'Listen',
        'listening_now': 'Reading...',

        # Footer
        'footer_text': 'Medical Intelligent Dialog System',
        'footer_powered': 'Powered by Self-Reasoning AI + Groq AI • Made with ',

        # Risk gauge
        'risk_gauge_title': 'Risk Level',

        # Session messages
        'session_started': 'New session started: {sid}',
        'start_session_first': 'Please start a new session first!',

        # Field names
        'field_names': {
            'age': 'Age',
            'gender': 'Gender',
            'height_cm': 'Height (cm)',
            'weight_kg': 'Weight (kg)',
            'bmi': 'BMI',
            'smoking_status': 'Smoking Status',
            'years_smoked': 'Years Smoked',
            'years_since_quit': 'Years Since Quit',
            'workplace_type': 'Workplace Type',
            'family_history': 'Family History',
            'hypertension': 'Hypertension',
            'diabetes': 'Diabetes',
            'cardiovascular_disease': 'Cardiovascular Disease',
            'chronic_diseases': 'Chronic Diseases',
            'obesity': 'Obesity',
            'gestational_diabetes': 'Gestational Diabetes',
            'hba1c': 'HbA1c',
            'cholesterol': 'Cholesterol',
        },
    },
}


# Sidebar writing examples HTML - per language
EXAMPLES_HTML = {
    'ar': """
    <style>
        .ex-card { background: #f8fafc; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px; border-right: 4px solid #6366f1; }
        .ex-card h4 { color: #4f46e5; margin: 0 0 6px 0; font-size: 13px; }
        .ex-row { display: flex; flex-wrap: wrap; gap: 5px; }
        .ex-chip { background: #e0e7ff; color: #3730a3; padding: 3px 8px; border-radius: 12px; font-size: 12px; white-space: nowrap; }
        .ex-chip.en { background: #dbeafe; color: #1e40af; }
        .ex-section { margin-bottom: 12px; }
        .ex-section-title { color: #6366f1; font-weight: bold; font-size: 14px; margin-bottom: 8px; padding-bottom: 4px; border-bottom: 2px solid #e0e7ff; }
        .ex-full { background: linear-gradient(135deg, #ede9fe, #e0e7ff); border-radius: 8px; padding: 10px 12px; margin-top: 10px; border-right: 4px solid #7c3aed; }
        .ex-full h4 { color: #7c3aed; margin: 0 0 6px 0; font-size: 13px; }
        .ex-full code { display: block; background: #fff; padding: 8px; border-radius: 6px; font-size: 11px; line-height: 1.6; white-space: pre-wrap; color: #334155; }
    </style>
    <div class="ex-section">
        <div class="ex-section-title">معلومات أساسية</div>
        <div class="ex-card"><h4>العمر</h4><div class="ex-row"><span class="ex-chip">عمري 55 سنة</span><span class="ex-chip">أبلغ 62 عاماً</span><span class="ex-chip en">Age 70</span><span class="ex-chip en">I am 45 years old</span><span class="ex-chip">العمر: 58</span></div></div>
        <div class="ex-card"><h4>الجنس</h4><div class="ex-row"><span class="ex-chip">ذكر</span><span class="ex-chip">أنثى</span><span class="ex-chip">رجل</span><span class="ex-chip">امرأة</span><span class="ex-chip en">Male</span><span class="ex-chip en">Female</span><span class="ex-chip en">M / F</span></div></div>
        <div class="ex-card"><h4>الطول</h4><div class="ex-row"><span class="ex-chip">طولي 175 سم</span><span class="ex-chip">168 سنتيمتر</span><span class="ex-chip">1.80 متر</span><span class="ex-chip en">Height 170 cm</span></div></div>
        <div class="ex-card"><h4>الوزن</h4><div class="ex-row"><span class="ex-chip">وزني 95 كيلو</span><span class="ex-chip">72 كيلوغرام</span><span class="ex-chip en">Weight 80 kg</span></div></div>
        <div class="ex-card"><h4>مؤشر كتلة الجسم (BMI)</h4><div class="ex-row"><span class="ex-chip">مؤشر كتلة الجسم 32</span><span class="ex-chip">يُحسب تلقائياً من الطول والوزن</span><span class="ex-chip en">BMI 28</span></div></div>
    </div>
    <div class="ex-section">
        <div class="ex-section-title">٢. التدخين</div>
        <div class="ex-card"><h4>حالة التدخين</h4><div class="ex-row"><span class="ex-chip">غير مدخّن</span><span class="ex-chip">مدخّن سابق</span><span class="ex-chip">مدخّن حالي</span><span class="ex-chip en">Non / Ex / Current smoker</span></div></div>
        <div class="ex-card"><h4>سنوات التدخين</h4><div class="ex-row"><span class="ex-chip">أدخّن من 30 سنة</span><span class="ex-chip">دخّنت 20 سنة</span><span class="ex-chip en">smoked for 15 years</span></div></div>
        <div class="ex-card"><h4>سنوات منذ الإقلاع</h4><div class="ex-row"><span class="ex-chip">أقلعت قبل 5 سنوات</span><span class="ex-chip">توقفت منذ سنتين</span><span class="ex-chip en">quit 5 years ago</span></div></div>
    </div>
    <div class="ex-section">
        <div class="ex-section-title">٣. العمل والوراثة</div>
        <div class="ex-card"><h4>نوع مكان العمل</h4><div class="ex-row"><span class="ex-chip">أعمل بمكتب</span><span class="ex-chip">أعمل بمصنع</span><span class="ex-chip en">Office / Factory</span></div></div>
        <div class="ex-card"><h4>التاريخ العائلي</h4><div class="ex-row"><span class="ex-chip">يوجد تاريخ عائلي</span><span class="ex-chip">لا يوجد في العائلة</span><span class="ex-chip en">Family history: Yes/No</span></div></div>
    </div>
    <div class="ex-section">
        <div class="ex-section-title">٤. الأمراض (نعم / لا)</div>
        <div class="ex-card"><h4>ارتفاع ضغط الدم</h4><div class="ex-row"><span class="ex-chip">عندي ضغط</span><span class="ex-chip">لا أعاني من الضغط</span><span class="ex-chip en">hypertension</span></div></div>
        <div class="ex-card"><h4>السكري</h4><div class="ex-row"><span class="ex-chip">مصاب بالسكري</span><span class="ex-chip">لا يوجد سكري</span><span class="ex-chip en">diabetes</span></div></div>
        <div class="ex-card"><h4>أمراض القلب والأوعية</h4><div class="ex-row"><span class="ex-chip">عندي أمراض قلب</span><span class="ex-chip">لا أمراض قلب</span><span class="ex-chip en">heart disease</span></div></div>
        <div class="ex-card"><h4>أمراض مزمنة</h4><div class="ex-row"><span class="ex-chip">عندي أمراض مزمنة</span><span class="ex-chip">لا أمراض مزمنة</span><span class="ex-chip en">chronic diseases</span></div></div>
        <div class="ex-card"><h4>السمنة</h4><div class="ex-row"><span class="ex-chip">عندي سمنة</span><span class="ex-chip">لا سمنة</span><span class="ex-chip en">obesity</span></div></div>
        <div class="ex-card"><h4>سكري الحمل (للنساء)</h4><div class="ex-row"><span class="ex-chip">سكري حمل سابق</span><span class="ex-chip">لا يوجد</span><span class="ex-chip en">gestational diabetes</span></div></div>
    </div>
    <div class="ex-section">
        <div class="ex-section-title">٥. التحاليل</div>
        <div class="ex-card"><h4>السكر التراكمي (HbA1c)</h4><div class="ex-row"><span class="ex-chip">السكر التراكمي 8.5</span><span class="ex-chip">التراكمي 5.4</span><span class="ex-chip en">HbA1c 6.5</span></div></div>
        <div class="ex-card"><h4>الكوليسترول</h4><div class="ex-row"><span class="ex-chip">الكوليسترول 280</span><span class="ex-chip">الكوليسترول 175</span><span class="ex-chip en">cholesterol 240</span></div></div>
    </div>
    <div class="ex-full" style="border-right-color:#7c3aed;"><h4 style="color:#7c3aed;">⭐ مثال شامل — كل الـ 18 حقل (مُختبَر ✓)</h4><code>أنثى عمري 62 سنة، الطول 160 والوزن 82، مؤشر كتلة الجسم 32،\nمدخّنة سابقة دخّنت 20 سنة وأقلعت قبل 5 سنوات، أعمل بمصنع،\nعندي ضغط وسكري وأمراض قلب وأمراض مزمنة وسمنة وسكري حمل سابق،\nالسكر التراكمي 7.5، الكوليسترول 260، ويوجد تاريخ عائلي.</code></div>

    <div class="ex-full" style="margin-top:8px; border-right-color:#dc2626;"><h4 style="color:#dc2626;">🔴 مثال عالي الخطر</h4><code>عمري 67 سنة، ذكر، الطول 175 سم، الوزن 98 كيلو،\nمدخّن حالي من 30 سنة، أعمل في مصنع،\nعندي ارتفاع ضغط وسكري وأمراض قلب وأمراض مزمنة وسمنة،\nالسكر التراكمي 8.5، الكوليسترول 280، ويوجد تاريخ عائلي.</code></div>

    <div class="ex-full" style="margin-top:8px; border-right-color:#16a34a;"><h4 style="color:#16a34a;">🟢 مثال منخفض الخطر (كل الـ 18)</h4><code>عمري 35 سنة، أنثى، الطول 165 سم، الوزن 58 كيلو، غير مدخّنة،\nأعمل في مكتب، لا ضغط ولا سكري ولا أمراض قلب ولا أمراض مزمنة ولا سمنة ولا سكري حمل،\nالسكر التراكمي 5.2، الكوليسترول 175، لا يوجد تاريخ عائلي.</code></div>
    """,

    'en': """
    <style>
        .ex-card { background: #f8fafc; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px; border-left: 4px solid #6366f1; }
        .ex-card h4 { color: #4f46e5; margin: 0 0 6px 0; font-size: 13px; }
        .ex-row { display: flex; flex-wrap: wrap; gap: 5px; }
        .ex-chip { background: #dbeafe; color: #1e40af; padding: 3px 8px; border-radius: 12px; font-size: 12px; white-space: nowrap; }
        .ex-chip.ar { background: #e0e7ff; color: #3730a3; }
        .ex-section { margin-bottom: 12px; }
        .ex-section-title { color: #6366f1; font-weight: bold; font-size: 14px; margin-bottom: 8px; padding-bottom: 4px; border-bottom: 2px solid #e0e7ff; }
        .ex-full { background: linear-gradient(135deg, #dbeafe, #e0e7ff); border-radius: 8px; padding: 10px 12px; margin-top: 10px; border-left: 4px solid #2563eb; }
        .ex-full h4 { color: #2563eb; margin: 0 0 6px 0; font-size: 13px; }
        .ex-full code { display: block; background: #fff; padding: 8px; border-radius: 6px; font-size: 11px; line-height: 1.6; white-space: pre-wrap; color: #334155; }
    </style>
    <div class="ex-section">
        <div class="ex-section-title">Basic Information</div>
        <div class="ex-card"><h4>Age</h4><div class="ex-row"><span class="ex-chip">I am 55 years old</span><span class="ex-chip">Age 62</span><span class="ex-chip">70 years old</span><span class="ex-chip ar">عمري 55 سنة</span></div></div>
        <div class="ex-card"><h4>Gender</h4><div class="ex-row"><span class="ex-chip">Male</span><span class="ex-chip">Female</span><span class="ex-chip">M / F</span><span class="ex-chip ar">ذكر</span><span class="ex-chip ar">أنثى</span></div></div>
        <div class="ex-card"><h4>Height</h4><div class="ex-row"><span class="ex-chip">Height 175 cm</span><span class="ex-chip">168 cm</span><span class="ex-chip">1.80 m</span><span class="ex-chip ar">طولي 175 سم</span></div></div>
        <div class="ex-card"><h4>Weight</h4><div class="ex-row"><span class="ex-chip">Weight 80 kg</span><span class="ex-chip">95 kilograms</span><span class="ex-chip ar">وزني 95 كيلو</span></div></div>
        <div class="ex-card"><h4>BMI</h4><div class="ex-row"><span class="ex-chip">BMI 28</span><span class="ex-chip">auto-computed from height/weight</span><span class="ex-chip ar">مؤشر كتلة الجسم 32</span></div></div>
    </div>
    <div class="ex-section">
        <div class="ex-section-title">2. Smoking</div>
        <div class="ex-card"><h4>Smoking Status</h4><div class="ex-row"><span class="ex-chip">Non-smoker</span><span class="ex-chip">Ex-smoker</span><span class="ex-chip">Current smoker</span></div></div>
        <div class="ex-card"><h4>Years Smoked</h4><div class="ex-row"><span class="ex-chip">smoked for 30 years</span><span class="ex-chip ar">أدخّن من 30 سنة</span></div></div>
        <div class="ex-card"><h4>Years Since Quit</h4><div class="ex-row"><span class="ex-chip">quit 5 years ago</span><span class="ex-chip ar">أقلعت قبل 5 سنوات</span></div></div>
    </div>
    <div class="ex-section">
        <div class="ex-section-title">3. Work & Heredity</div>
        <div class="ex-card"><h4>Workplace Type</h4><div class="ex-row"><span class="ex-chip">Office</span><span class="ex-chip">Factory</span><span class="ex-chip ar">مكتب / مصنع</span></div></div>
        <div class="ex-card"><h4>Family History</h4><div class="ex-row"><span class="ex-chip">Family history: Yes</span><span class="ex-chip">No family history</span></div></div>
    </div>
    <div class="ex-section">
        <div class="ex-section-title">4. Conditions (yes / no)</div>
        <div class="ex-card"><h4>Hypertension</h4><div class="ex-row"><span class="ex-chip">I have high blood pressure</span><span class="ex-chip">no hypertension</span></div></div>
        <div class="ex-card"><h4>Diabetes</h4><div class="ex-row"><span class="ex-chip">I am diabetic</span><span class="ex-chip">no diabetes</span></div></div>
        <div class="ex-card"><h4>Cardiovascular Disease</h4><div class="ex-row"><span class="ex-chip">I have heart disease</span><span class="ex-chip">no heart disease</span></div></div>
        <div class="ex-card"><h4>Chronic Diseases</h4><div class="ex-row"><span class="ex-chip">I have chronic conditions</span><span class="ex-chip">none</span></div></div>
        <div class="ex-card"><h4>Obesity</h4><div class="ex-row"><span class="ex-chip">obese</span><span class="ex-chip">not obese</span></div></div>
        <div class="ex-card"><h4>Gestational Diabetes (women)</h4><div class="ex-row"><span class="ex-chip">past gestational diabetes</span><span class="ex-chip">none</span></div></div>
    </div>
    <div class="ex-section">
        <div class="ex-section-title">5. Labs</div>
        <div class="ex-card"><h4>HbA1c</h4><div class="ex-row"><span class="ex-chip">HbA1c 8.5</span><span class="ex-chip">A1c 5.4</span></div></div>
        <div class="ex-card"><h4>Cholesterol</h4><div class="ex-row"><span class="ex-chip">cholesterol 280</span><span class="ex-chip">cholesterol 175</span></div></div>
    </div>
    <div class="ex-full" style="border-left-color:#7c3aed;"><h4 style="color:#7c3aed;">⭐ Comprehensive — all 18 fields (verified ✓)</h4><code>Female, 62 years old, height 160 cm, weight 82 kg, BMI 32,\nex-smoker who smoked 20 years and quit 5 years ago, work in a factory,\nI have hypertension, diabetes, heart disease, chronic diseases, obesity and past gestational diabetes,\nHbA1c 7.5, cholesterol 260, family history yes.</code></div>

    <div class="ex-full" style="margin-top:8px; border-left-color:#dc2626;"><h4 style="color:#dc2626;">🔴 High-risk</h4><code>I am 67 years old, male, height 175 cm, weight 98 kg,\ncurrent smoker for 30 years, work in a factory,\nI have hypertension, diabetes, heart disease, chronic diseases and obesity,\nHbA1c 8.5, cholesterol 280, family history yes.</code></div>

    <div class="ex-full" style="margin-top:8px; border-left-color:#16a34a;"><h4 style="color:#16a34a;">🟢 Low-risk (all 18)</h4><code>I am 35 years old, female, height 165 cm, weight 58 kg, non-smoker,\nwork in an office, no hypertension, no diabetes, no heart disease, no chronic diseases, not obese, no gestational diabetes,\nHbA1c 5.2, cholesterol 175, no family history.</code></div>
    """,
}


def t(key, lang='ar'):
    """Get translated text by key"""
    return UI_TEXT.get(lang, UI_TEXT['ar']).get(key, key)


def get_field_name(field, lang='ar'):
    """Get translated field name"""
    names = UI_TEXT.get(lang, UI_TEXT['ar']).get('field_names', {})
    return names.get(field, field)


def get_field_names_dict(lang='ar'):
    """Get all field names as dict"""
    return UI_TEXT.get(lang, UI_TEXT['ar']).get('field_names', {})
