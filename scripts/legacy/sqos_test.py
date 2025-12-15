# sqos_test.py

import yaml
import re

class SQOS:
    def __init__(self, main_prompt_path, confusion_analyzer_path, question_generator_path, case_library_path):
        self.main_prompt_content = self._read_file_content(main_prompt_path)
        self.confusion_analyzer_content = self._read_file_content(confusion_analyzer_path)
        self.question_generator_content = self._read_file_content(question_generator_path)
        self.case_library = self._load_yaml(case_library_path)

        self.main_prompt_config = self._parse_main_prompt_for_question_types(self.main_prompt_content)
        self.confusion_analyzer_config = self._extract_yaml_from_markdown(self.confusion_analyzer_content)
        self.question_generator_config = self._extract_yaml_from_markdown(self.question_generator_content)

    def _read_file_content(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _load_yaml(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _extract_yaml_from_markdown(self, markdown_content):
        # Extracts YAML blocks from markdown files
        yaml_blocks = re.findall(r'```yaml\n([\s\S]*?)\n```', markdown_content)
        full_yaml = "\n".join(yaml_blocks)
        return yaml.safe_load(full_yaml) if full_yaml else {}

    def _parse_main_prompt_for_question_types(self, markdown_content):
        # Manually parse the '问题类型定义' section from the main prompt markdown
        question_type_definitions = {}
        # Pattern to find '### X. YYY型问题' sections and their '目的'
        pattern = r'### \d\. (.*?型问题)\n.*?-\s\*\*目的\*\*：\s*(.*?)\n'
        matches = re.findall(pattern, markdown_content, re.DOTALL)
        for q_type, purpose in matches:
            question_type_definitions[q_type] = {'目的': purpose.strip()}
        return {'问题类型定义': question_type_definitions}

    def analyze_confusion(self, user_input):
        # Implement confusion analysis based on confusion_analyzer_config
        # This is a simplified placeholder. A full implementation would involve
        # concept extraction, misconception detection, multi-question separation, etc.
        
        core_concepts = []
        domain = ""
        user_level = "初学者"
        confusion_type = "概念理解"
        misconceptions = []

        # Simple keyword-based concept extraction and domain inference
        if re.search(r'static|class|method|public|void|String\[\]', user_input, re.IGNORECASE):
            domain = "Java编程"
            if re.search(r'static', user_input, re.IGNORECASE):
                core_concepts.append({'concept': 'static', 'context': '关键字使用', 'confidence': 0.9})
                # Use misconception patterns from config if available
                static_misconceptions = self.confusion_analyzer_config.get('误解模式库', {}).get('static相关', [])
                for mc_pattern in static_misconceptions:
                    if re.search(mc_pattern['模式'], user_input):
                        misconceptions.append({'type': mc_pattern['误解类型'], 'detail': mc_pattern['正确理解'], 'severity': 'high'})
            if re.search(r'class', user_input, re.IGNORECASE):
                core_concepts.append({'concept': 'class', 'context': '定义对象模板', 'confidence': 0.9})
                class_misconceptions = self.confusion_analyzer_config.get('误解模式库', {}).get('class相关', [])
                for mc_pattern in class_misconceptions:
                    if re.search(mc_pattern['模式'], user_input):
                        misconceptions.append({'type': mc_pattern['误解类型'], 'detail': mc_pattern['正确理解'], 'severity': 'medium'})
            if re.search(r'main method|main', user_input, re.IGNORECASE):
                core_concepts.append({'concept': 'main method', 'context': '程序入口', 'confidence': 1.0})
            if re.search(r'String\[\] args|args', user_input, re.IGNORECASE):
                core_concepts.append({'concept': 'String[] args', 'context': '命令行参数', 'confidence': 1.0})
                args_misconceptions = self.confusion_analyzer_config.get('误解模式库', {}).get('参数相关', [])
                for mc_pattern in args_misconceptions:
                    if re.search(mc_pattern['模式'], user_input):
                        misconceptions.append({'type': mc_pattern['误解类型'], 'detail': mc_pattern['正确理解'], 'severity': 'high'})
        elif re.search(r'递归', user_input):
            domain = "算法思维"
            core_concepts.append({'concept': '递归', 'context': '算法概念', 'confidence': 1.0})
            if re.search(r'停下来', user_input): # This specific misconception is not in the YAML, so keep it for now
                misconceptions.append({'type': '实现困难', 'detail': '不理解递归终止条件', 'severity': 'high'})
        elif re.search(r'数组|链表', user_input):
            domain = "数据结构"
            core_concepts.append({'concept': '数组/链表', 'context': '数据结构', 'confidence': 1.0})
        elif re.search(r'继承', user_input):
            domain = "面向对象编程"
            core_concepts.append({'concept': '继承', 'context': 'OOP概念', 'confidence': 1.0})

        # Determine confusion type based on keywords
        if re.search(r'区别|不同|对比', user_input):
            confusion_type = "对比差异"
        elif re.search(r'怎么用|如何实现|例子', user_input):
            confusion_type = "使用方法"
        elif re.search(r'为什么|原理|设计初衷', user_input):
            confusion_type = "原理探究"

        return {
            'raw_input': user_input,
            'core_concepts': core_concepts,
            'misconceptions': misconceptions,
            'confusion_type': confusion_type,
            'domain': domain,
            'user_level': user_level,
            'sub_questions': [], # Simplified, not implementing multi-question separation yet
            'focus_suggestion': ""
        }

    def generate_questions(self, confusion_analysis_result):
        # Implement question generation based on question_generator_config
        # This is a simplified placeholder
        
        core_concept = confusion_analysis_result['core_concepts'][0]['concept'] if confusion_analysis_result['core_concepts'] else "X"
        confusion_type = confusion_analysis_result['confusion_type']
        domain = confusion_analysis_result['domain']

        generated_questions = []
        # Accessing type_weights_by_confusion from the extracted YAML config
        question_type_weights = self.question_generator_config.get('type_weights_by_confusion', {})
        
        # Prioritize question types based on confusion type
        sorted_question_types = sorted(question_type_weights.items(), key=lambda item: item[1], reverse=True)
        
        # Ensure diversity by picking from different types
        selected_types_count = 0
        for q_type, _ in sorted_question_types:
            # Ensure we don't add more than 5 questions total
            if len(generated_questions) >= 5:
                break

            # Only add if this type hasn't been added or if we need more unique types
            if q_type not in [q['type'] for q in generated_questions] or selected_types_count < 3:
                selected_types_count += 1
                
                # Get templates from the config, adjusting key name to match YAML structure
                template_key = f'{q_type.replace("型问题", "").lower()}_templates' # e.g., '对比型问题' -> '对比_templates' -> 'comparison_templates'
                templates = self.question_generator_config.get(template_key, {})
                
                # Pick one template from each category for diversity, or just the first if category not explicit
                added_for_type = 0
                for template_category in templates:
                    if len(generated_questions) >= 5 or added_for_type >= 1: # Limit to 1 question per type from initial pass for diversity
                        break
                    template_str = templates[template_category][0]
                    question_text = template_str.replace('{concept}', core_concept).replace('{concept1}', core_concept).replace('{concept2}', 'Y').replace('{action}', '此概念').replace('{feature}', core_concept).replace('{language/framework}', domain)
                    generated_questions.append({
                        'text': question_text,
                        'type': q_type,
                        'explanation': self.main_prompt_config['问题类型定义'][q_type]['目的'],
                    })
                    added_for_type += 1

        # Fallback to generic if not enough questions generated or if specific domain templates are not found
        if len(generated_questions) < 5:
            generic_types = ["对比型", "演示型", "定义型", "原因型", "应用型"]
            for q_type_short in generic_types:
                q_type_full = f'{q_type_short}问题' # Reconstruct full type name to match main_prompt_config
                if len(generated_questions) >= 5:
                    break
                if q_type_full not in [q['type'] for q in generated_questions]:
                    template_key = f'{q_type_short.lower()}_templates'
                    templates = self.question_generator_config.get(template_key, {})
                    if templates:
                        template_str = list(templates.values())[0][0] # Get first template from first category
                        question_text = template_str.replace('{concept}', core_concept).replace('{concept1}', core_concept).replace('{concept2}', 'Y').replace('{action}', '此概念').replace('{feature}', core_concept).replace('{language/framework}', domain)
                        generated_questions.append({
                            'text': question_text,
                            'type': q_type_full,
                            'explanation': self.main_prompt_config['问题类型定义'][q_type_full]['目的'],
                        })
        
        return generated_questions[:5]

    def format_output(self, user_input, questions):
        output = f"基于你的困惑：\"{user_input}\"\n\n我为你生成了以下精准问题，请选择最符合你需求的：\n\n"
        
        # Retrieve explanations from the parsed main_prompt_config
        type_explanations = {}
        for q_type_full, details in self.main_prompt_config['问题类型定义'].items():
            # Remove the "问题" suffix for matching with q['type']
            short_type = q_type_full.replace("问题", "")
            type_explanations[short_type] = f"💡 {details['目的']}"

        for i, q in enumerate(questions):
            # q['type'] will be something like "对比型问题", but our keys are "对比型"
            display_type = q['type'].replace("问题", "") # Get "对比型" from "对比型问题" for display
            output += f"{i+1}. 【{display_type}】{q['text']}\n"
            output += f"   {type_explanations.get(display_type, '')}\n\n"
        output += "输入数字选择问题，或输入0自定义你的问题。"
        return output

# Example Usage
if __name__ == "__main__":
    sqos_system = SQOS(
        main_prompt_path='prompts/sqos-main-prompt.md',
        confusion_analyzer_path='prompts/modules/confusion-analyzer.md',
        question_generator_path='prompts/modules/question-generator.md',
        case_library_path='prompts/data/cs61b-case-library.yaml'
    )

    test_confusions = [
        "我搞不懂static",
        "main method里面的String[] args是什么",
        "我不懂class和类的difference",
        "递归怎么理解",
        "数组和链表有什么区别",
        "为什么Java要try-catch，直接让程序崩溃不行吗？"
    ]

    for confusion in test_confusions:
        print("\n" + "="*50)
        print(f"Processing confusion: \"{confusion}\"")
        analysis = sqos_system.analyze_confusion(confusion)
        questions = sqos_system.generate_questions(analysis)
        formatted_output = sqos_system.format_output(confusion, questions)
        print(formatted_output)
