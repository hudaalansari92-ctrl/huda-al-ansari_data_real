

# قاموس الأمثلة لكل سؤال — الحقول السريرية الأصل الـ 8 (bmi محسوب تلقائياً)
QUESTION_EXAMPLES = {
    'age': {
        'question_ar': 'كم عمرك؟',
        'question_en': 'What is your age?',
        'examples_ar': [
            '55',
            'عمري 55 سنة',
            'أنا أبلغ من العمر 62 عاماً',
            '45 سنة'
        ],
        'examples_en': [
            '55',
            'I am 55 years old',
            '45 years',
            'Age: 62'
        ],
        'tips_ar': 'اكتب عمرك بالأرقام (مثل: 55)',
        'is_first': True  # هذا هو السؤال الأول دائماً
    },

    'gender': {
        'question_ar': 'ما جنسك؟',
        'question_en': 'What is your gender?',
        'examples_ar': [
            'ذكر',
            'أنثى',
            'Male',
            'Female'
        ],
        'examples_en': [
            'Male',
            'Female',
            'M',
            'F'
        ],
        'tips_ar': 'اكتب: ذكر أو أنثى'
    },

    'height_cm': {
        'question_ar': 'كم طولك بالسنتيمتر؟',
        'question_en': 'What is your height in centimeters?',
        'examples_ar': [
            '170',
            'طولي 175 سم',
            '168 سنتيمتر',
            '1.80 متر'
        ],
        'examples_en': [
            '170',
            'I am 175 cm tall',
            'Height: 168 cm',
            '1.80 m'
        ],
        'tips_ar': 'اكتب الطول بالسنتيمتر (مثل: 175)'
    },

    'weight_kg': {
        'question_ar': 'كم وزنك بالكيلوغرام؟',
        'question_en': 'What is your weight in kilograms?',
        'examples_ar': [
            '80',
            'وزني 95 كيلو',
            '72 كيلوغرام',
            'الوزن 88'
        ],
        'examples_en': [
            '80',
            'I weigh 95 kg',
            'Weight: 72 kg',
            '88 kilograms'
        ],
        'tips_ar': 'اكتب الوزن بالكيلوغرام (مثل: 80)'
    },

    'smoking_status': {
        'question_ar': 'ما حالتك مع التدخين؟ (غير مدخّن / مدخّن سابق / مدخّن حالي)',
        'question_en': 'What is your smoking status? (non-smoker / ex-smoker / current smoker)',
        'examples_ar': [
            'غير مدخّن',
            'مدخّن سابق',
            'مدخّن حالي',
            'أدخّن حالياً',
            'أقلعت عن التدخين'
        ],
        'examples_en': [
            'Non-smoker',
            'Ex-smoker',
            'Current smoker',
            'I quit smoking',
            'I smoke now'
        ],
        'tips_ar': 'اكتب: غير مدخّن، مدخّن سابق، أو مدخّن حالي'
    },

    'workplace_type': {
        'question_ar': 'ما نوع مكان عملك؟ (مكتب / مصنع)',
        'question_en': 'What is your workplace type? (office / factory)',
        'examples_ar': [
            'مكتب',
            'مصنع',
            'أعمل في مكتب',
            'أعمل في مصنع'
        ],
        'examples_en': [
            'Office',
            'Factory',
            'I work in an office',
            'I work in a factory'
        ],
        'tips_ar': 'اكتب: مكتب أو مصنع'
    },

    'environmental_hazards': {
        'question_ar': 'هل تتعرّض لأي مخاطر بيئية في عملك؟ (توتر، تلوّث، ضوضاء، غبار، مواد كيميائية، عمل بنظام الورديات)',
        'question_en': 'Are you exposed to any environmental hazards at work? (stress, pollution, noise, dust, chemicals, shift work)',
        'examples_ar': [
            'توتر',
            'غبار ومواد كيميائية',
            'ضوضاء وتلوّث',
            'عمل بنظام الورديات',
            'لا يوجد'
        ],
        'examples_en': [
            'Stress',
            'Dust and chemicals',
            'Noise and pollution',
            'Shift work',
            'None'
        ],
        'tips_ar': 'اذكر المخاطر المنطبقة، أو اكتب: لا يوجد'
    },

    'family_history': {
        'question_ar': 'هل يوجد تاريخ عائلي لأمراض القلب؟',
        'question_en': 'Is there a family history of heart disease?',
        'examples_ar': [
            'نعم',
            'لا',
            'يوجد تاريخ عائلي',
            'لا يوجد في العائلة'
        ],
        'examples_en': [
            'Yes',
            'No',
            'Yes, family history present',
            'No family history'
        ],
        'tips_ar': 'اكتب: نعم أو لا'
    },

    'bmi': {
        'question_ar': 'ما مؤشر كتلة جسمك (BMI) إن كنت تعرفه؟ (أو اتركه ليُحسب من الطول والوزن)',
        'question_en': 'Your BMI if known? (or leave it to be computed from height/weight)',
        'examples_ar': ['27', '32', 'لا أعرف'],
        'examples_en': ['27', '32', "don't know"],
        'tips_ar': 'رقم تقريبي أو اتركه'
    },
    'years_smoked': {
        'question_ar': 'كم سنة دخّنت (إن كنت مدخّناً أو سابقاً)؟',
        'question_en': 'How many years have you smoked (if current/ex-smoker)?',
        'examples_ar': ['10', '20 سنة', 'لا أدخّن'],
        'examples_en': ['10', '20 years', 'never smoked'],
        'tips_ar': 'عدد السنوات أو 0'
    },
    'years_since_quit': {
        'question_ar': 'كم سنة مضت منذ أن أقلعت عن التدخين؟',
        'question_en': 'How many years since you quit smoking?',
        'examples_ar': ['5', '0', 'لم أقلع'],
        'examples_en': ['5', '0', "haven't quit"],
        'tips_ar': 'عدد السنوات أو 0'
    },
    'hypertension': {
        'question_ar': 'هل تعاني من ارتفاع ضغط الدم؟',
        'question_en': 'Do you have hypertension (high blood pressure)?',
        'examples_ar': ['نعم', 'لا', 'عندي ضغط'],
        'examples_en': ['Yes', 'No', 'I have high blood pressure'],
        'tips_ar': 'اكتب: نعم أو لا'
    },
    'diabetes': {
        'question_ar': 'هل أنت مصاب بالسكري؟',
        'question_en': 'Do you have diabetes?',
        'examples_ar': ['نعم', 'لا', 'عندي سكري'],
        'examples_en': ['Yes', 'No', 'I am diabetic'],
        'tips_ar': 'اكتب: نعم أو لا'
    },
    'cardiovascular_disease': {
        'question_ar': 'هل لديك تشخيص بأمراض القلب أو الأوعية الدموية؟',
        'question_en': 'Have you been diagnosed with cardiovascular disease?',
        'examples_ar': ['نعم', 'لا', 'عندي مرض قلب'],
        'examples_en': ['Yes', 'No', 'I have heart disease'],
        'tips_ar': 'اكتب: نعم أو لا'
    },
    'chronic_diseases': {
        'question_ar': 'هل تعاني من أي أمراض مزمنة؟',
        'question_en': 'Do you suffer from any chronic diseases?',
        'examples_ar': ['نعم', 'لا', 'عندي أمراض مزمنة'],
        'examples_en': ['Yes', 'No', 'I have chronic conditions'],
        'tips_ar': 'اكتب: نعم أو لا'
    },
    'obesity': {
        'question_ar': 'هل تعاني من السمنة؟ (أو اتركها لتُحسب من BMI)',
        'question_en': 'Are you obese? (or leave it to be derived from BMI)',
        'examples_ar': ['نعم', 'لا'],
        'examples_en': ['Yes', 'No'],
        'tips_ar': 'اكتب: نعم أو لا'
    },
    'gestational_diabetes': {
        'question_ar': 'هل لديك تاريخ سكري الحمل؟ (للنساء)',
        'question_en': 'Any history of gestational diabetes? (for women)',
        'examples_ar': ['نعم', 'لا', 'لا ينطبق'],
        'examples_en': ['Yes', 'No', 'N/A'],
        'tips_ar': 'اكتب: نعم أو لا'
    },
    'hba1c': {
        'question_ar': 'ما قيمة السكر التراكمي (HbA1c) لديك؟',
        'question_en': 'What is your HbA1c (%) value?',
        'examples_ar': ['5.5', '7', '8.2', 'لا أعرف'],
        'examples_en': ['5.5', '7', '8.2', "don't know"],
        'tips_ar': 'رقم مثل 6.5'
    },
    'cholesterol': {
        'question_ar': 'ما مستوى الكوليسترول لديك (mg/dL)؟',
        'question_en': 'What is your cholesterol level (mg/dL)?',
        'examples_ar': ['200', '250', '280', 'لا أعرف'],
        'examples_en': ['200', '250', '280', "don't know"],
        'tips_ar': 'رقم مثل 240'
    }
}


def get_question_info(field_name, language='ar'):
    """
    الحصول على معلومات السؤال
    
    Args:
        field_name: اسم الحقل
        language: اللغة ('ar' أو 'en')
    
    Returns:
        dict: معلومات السؤال
    """
    if field_name not in QUESTION_EXAMPLES:
        return None
    
    info = QUESTION_EXAMPLES[field_name]
    question_key = f'question_{language}'
    examples_key = f'examples_{language}'
    
    return {
        'field': field_name,
        'question': info.get(question_key, ''),
        'examples': info.get(examples_key, []),
        'tips': info.get(f'tips_{language}', ''),
        'is_first': info.get('is_first', False)
    }


def get_first_question(language='ar'):
    """
    الحصول على السؤال الأول (العمر)
    
    Args:
        language: اللغة
    
    Returns:
        dict: معلومات السؤال الأول
    """
    return get_question_info('age', language)


def format_examples_html(examples, max_count=4):
    """
    تنسيق الأمثلة كـ HTML
    
    Args:
        examples: قائمة الأمثلة
        max_count: أقصى عدد من الأمثلة للعرض
    
    Returns:
        str: HTML للأمثلة
    """
    if not examples:
        return ""
    
    examples_to_show = examples[:max_count]
    examples_list = "<br>".join([f"• {ex}" for ex in examples_to_show])
    
    return f"""
    <div style='margin-top: 10px; padding: 12px; background: rgba(156,39,176,0.08); 
                border-radius: 8px; border-left: 3px solid #9c27b0;'>
        <strong style='color: #7b1fa2;'> أمثلة على الإجابة:</strong><br>
        <span style='color: #555; font-size: 0.95rem;'>{examples_list}</span>
    </div>
    """
