import os
import django
import logging
from datetime import datetime

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from mcqs.models import MCQ

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s\nDetails: %(details)s\n',
    filename='mcq_validation_log.txt'
)
logger = logging.getLogger(__name__)

class MCQValidator:
    def __init__(self, mcq):
        self.mcq = mcq
        self.errors = []
        
    def get_mcq_identifier(self):
        """Get a string identifier for the MCQ, fallback to text if id is missing"""
        try:
            mcq_id = getattr(self.mcq, 'id', 'Unknown ID')
            question_text = (self.mcq.text[:100] + '...') if self.mcq.text and len(self.mcq.text) > 100 else self.mcq.text
            return f"MCQ(id={mcq_id}, text='{question_text}')"
        except AttributeError as e:
            return f"MCQ(text='{getattr(self.mcq, 'text', 'Unknown text')}')"
    
    def validate_question_text(self):
        """Check if question text is empty"""
        try:
            if not self.mcq.text or self.mcq.text.strip() == '' or self.mcq.text.strip() == 'Default question text':
                self.errors.append("Question text is empty or default")
                return False
            return True
        except AttributeError as e:
            self.errors.append(f"Question text validation error: {str(e)}")
            return False
    
    def validate_options(self):
        """Check if any option is empty"""
        try:
            empty_options = []
            
            if not self.mcq.option_1 or self.mcq.option_1.strip() == '':
                empty_options.append("Option 1")
            if not self.mcq.option_2 or self.mcq.option_2.strip() == '':
                empty_options.append("Option 2")
            if not self.mcq.option_3 or self.mcq.option_3.strip() == '':
                empty_options.append("Option 3")
            if not self.mcq.option_4 or self.mcq.option_4.strip() == '':
                empty_options.append("Option 4")
                
            if empty_options:
                self.errors.append(f"Empty options found: {', '.join(empty_options)}")
                return False
            return True
        except AttributeError as e:
            self.errors.append(f"Options validation error: {str(e)}")
            return False
    
    def validate_correct_answer(self):
        """Check if correct answer exists in options"""
        try:
            if not self.mcq.correct_option or self.mcq.correct_option.strip() == '':
                self.errors.append("Correct answer is empty")
                return False
                
            options = [
                self.mcq.option_1,
                self.mcq.option_2,
                self.mcq.option_3,
                self.mcq.option_4
            ]
            
            # Strip whitespace for comparison
            correct_answer = self.mcq.correct_option.strip()
            options = [opt.strip() if opt else '' for opt in options]
            
            if correct_answer not in options:
                self.errors.append("Correct answer does not match any option exactly")
                return False
            return True
        except AttributeError as e:
            self.errors.append(f"Correct answer validation error: {str(e)}")
            return False
    
    def validate_explanation(self):
        """Check if explanation is empty"""
        try:
            if not self.mcq.explanation or self.mcq.explanation.strip() == '':
                self.errors.append("Explanation is empty")
                return False
            return True
        except AttributeError as e:
            self.errors.append(f"Explanation validation error: {str(e)}")
            return False
    
    def validate(self):
        """Run all validations"""
        is_valid = True
        
        if not self.validate_question_text():
            is_valid = False
        if not self.validate_options():
            is_valid = False
        if not self.validate_correct_answer():
            is_valid = False
        if not self.validate_explanation():
            is_valid = False
            
        return is_valid, self.errors

def validate_all_mcqs():
    """Validate all MCQs in the database"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'mcq_validation_report_{timestamp}.txt'
    
    try:
        all_mcqs = MCQ.objects.all()
        invalid_mcqs = []
        
        print(f"Starting validation of {all_mcqs.count()} MCQs...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("MCQ Validation Report\n")
            f.write("===================\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total MCQs checked: {all_mcqs.count()}\n\n")
            
            for mcq in all_mcqs:
                validator = MCQValidator(mcq)
                try:
                    is_valid, errors = validator.validate()
                    
                    if not is_valid:
                        invalid_mcqs.append((mcq, errors))
                        
                        mcq_identifier = validator.get_mcq_identifier()
                        f.write(f"\n{mcq_identifier}\n")
                        f.write("Errors found:\n")
                        for error in errors:
                            f.write(f"- {error}\n")
                        
                        # Log full MCQ details with proper error handling
                        f.write("\nFull MCQ Details:\n")
                        try:
                            f.write(f"Question: {getattr(mcq, 'text', 'N/A')}\n")
                            f.write(f"Option 1: {getattr(mcq, 'option_1', 'N/A')}\n")
                            f.write(f"Option 2: {getattr(mcq, 'option_2', 'N/A')}\n")
                            f.write(f"Option 3: {getattr(mcq, 'option_3', 'N/A')}\n")
                            f.write(f"Option 4: {getattr(mcq, 'option_4', 'N/A')}\n")
                            f.write(f"Correct Answer: {getattr(mcq, 'correct_option', 'N/A')}\n")
                            f.write(f"Explanation: {getattr(mcq, 'explanation', 'N/A')}\n")
                        except Exception as e:
                            f.write(f"Error retrieving MCQ details: {str(e)}\n")
                        f.write("-" * 80 + "\n")
                
                except Exception as e:
                    logger.error(
                        "Error validating MCQ",
                        extra={
                            'details': f"MCQ: {validator.get_mcq_identifier()}\nError: {str(e)}"
                        }
                    )
            
            f.write("\nSummary:\n")
            f.write(f"Total MCQs with errors: {len(invalid_mcqs)}\n")
            f.write(f"Percentage valid: {((all_mcqs.count() - len(invalid_mcqs)) / all_mcqs.count() * 100):.2f}%\n")
        
        print(f"\nValidation complete. Results saved to {output_file}")
        print(f"Found {len(invalid_mcqs)} MCQs with errors out of {all_mcqs.count()} total MCQs")
        
        return invalid_mcqs
    
    except Exception as e:
        error_details = f"Error during validation process: {str(e)}"
        logger.error("Validation process failed", extra={'details': error_details})
        print(f"An error occurred. Check mcq_validation_log.txt for details.")
        return []

if __name__ == '__main__':
    try:
        invalid_mcqs = validate_all_mcqs()
        
        if invalid_mcqs:
            print("\nExample of errors found:")
            for mcq, errors in invalid_mcqs[:3]:  # Show first 3 examples
                validator = MCQValidator(mcq)
                print(f"\n{validator.get_mcq_identifier()}")
                print("Errors:")
                for error in errors:
                    print(f"- {error}")
    except Exception as e:
        logger.error("Main execution failed", extra={'details': str(e)})