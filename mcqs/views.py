from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from .models import Subject, Unit, Chapter, Topic
from django.http import JsonResponse
from .models import MCQ,TestSession, TestAnswer, difficulties,Bookmark
import json
from django.db.models import Q
# Create your views here.
from django.core.serializers import serialize
from rest_framework.renderers import JSONRenderer
from .serializers import MCQSerializer,MCQSubmitSerializer
import random
import uuid
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict
from django.http import HttpResponseRedirect,HttpResponse
from django.contrib import messages



@login_required(login_url='/')
def cus_mcq(request,email_token):
    if request.user.is_authenticated:
        print(request.user.profile.email_token)
        if email_token==request.user.profile.email_token:
            data = {}

            subjects = Subject.objects.all()
            for subject in subjects:
                units = Unit.objects.filter(subject=subject)
                data[subject.name] = {}

                for unit in units:
                    chapters = Chapter.objects.filter(unit=unit)
                    data[subject.name][unit.name] = {}

                    for chapter in chapters:
                        topics = Topic.objects.filter(chapter=chapter)
                        data[subject.name][unit.name][chapter.name] = [topic.name for topic in topics]

            context = {
                'data': data
            }
            return render(request, 'customemcq/cusmcq.html', context)
        else:
            print("hello")





from django.db.models import Q
import uuid
import json
import random
from decimal import Decimal

from django.db.models import Q
import uuid
import json
import random

import random

import random

@login_required(login_url='/')
def test(request, email_token):
    profile = request.user.profile
    if not profile.current_test:

        user = request.user
        test_id = str(uuid.uuid4())
        
        selections_json = request.GET.get('selections')
        selections = json.loads(selections_json) if selections_json else []
        if not selections:
            messages.error(request, "Please add selections by clicking on 'Add Selection' after making your choices.")
            return HttpResponseRedirect(f'/{email_token}/mcq/')
        question_type = request.GET.get('questionType').title()
        difficulty_level = request.GET.get('difficultyLevel').title()
        num_mcqs_str = request.GET.get('numQuestions', '25')
        try:
            num_mcqs = round(float(num_mcqs_str))  # Round to the nearest integer
        except ValueError:
            num_mcqs = 25  # Default to 25 if input is invalid or missing
        
        time_per_question_str = request.GET.get('timePerQuestion')
        try:
            time_per_question = float(time_per_question_str) if time_per_question_str else 1.0  # Default to 1 minute if None
            # Ensure it's within the minimum and maximum limits
            if time_per_question < 0.6:
                time_per_question = 0.6
            elif time_per_question > 3:
                time_per_question = 3
        except ValueError:
            # Set to 1 minute if conversion fails
            time_per_question = 1.0
        

        # Alert if number of questions requested exceeds 40
        if num_mcqs > 40:
            messages.error(request, "You cannot select more than 40 questions.")
            return HttpResponseRedirect('/7bee884d-342b-4713-87c1-baf10612d296/mcq/')


        selections_data = []

        # Step 1: Build queries for each selection
        for selection in selections:
            parts = selection.split('-')
            subject_name = parts[0]
            
            if len(parts) == 1:
                query = Q(topic__chapter__unit__subject__name=subject_name)
            elif len(parts) == 2:
                unit_name = parts[1]
                query = Q(topic__chapter__unit__subject__name=subject_name, topic__chapter__unit__name=unit_name)
            elif len(parts) == 3:
                unit_name, chapter_name = parts[1], parts[2]
                query = Q(topic__chapter__unit__subject__name=subject_name, topic__chapter__unit__name=unit_name, topic__chapter__name=chapter_name)
            elif len(parts) == 4:
                unit_name, chapter_name, topic_name = parts[1], parts[2], parts[3]
                query = Q(topic__chapter__unit__subject__name=subject_name, topic__chapter__unit__name=unit_name, topic__chapter__name=chapter_name, topic__name=topic_name)
            else:
                continue

            # Apply question type and difficulty level filters
            if question_type and question_type != "Mixed":
                query &= Q(types__types=question_type)
            if difficulty_level and difficulty_level != "Mixed":
                query &= Q(difficulty__name=difficulty_level)
            
            selections_data.append({
                'selection': selection,
                'query': query,
                'parts_count': len(parts)
            })

        # Step 2: Gather all filtered MCQs based on selections and shuffle powerfully
        filtered_mcqs = []
        for selection_data in selections_data:
            filtered_mcqs.extend(MCQ.objects.filter(selection_data['query']))
        filtered_mcqs = list(set(filtered_mcqs))  # Remove duplicates
        random.shuffle(filtered_mcqs)  # Powerful shuffle for variety
        print("filtered:",len(filtered_mcqs))
        # Step 3: Calculate inverse weight and allocate MCQs by selection parts

        if len(filtered_mcqs) == 0:
            messages.error(request, "No MCQs found with the current selections and filters. Please adjust your criteria.")
            return HttpResponseRedirect('/7bee884d-342b-4713-87c1-baf10612d296/mcq/')


        inverse_parts_count_sum = sum(1 / data['parts_count'] for data in selections_data)
        final_mcqs = []
        mcqs_count_by_selection = {}

        for selection_data in selections_data:
            parts_count = selection_data['parts_count']
            inverse_weight = (1 / parts_count) / inverse_parts_count_sum
            allocated_mcqs_count = round(inverse_weight * num_mcqs)
            
            # Select and add to final_mcqs, ensuring no duplicates
            selected_mcqs = [mcq for mcq in filtered_mcqs if mcq not in final_mcqs][:allocated_mcqs_count]
            final_mcqs.extend(selected_mcqs)

            # Record and print the count of MCQs for this selection
            mcqs_count_by_selection[selection_data['selection']] = len(selected_mcqs)
            print(f"Allocated MCQs from selection '{selection_data['selection']}': {len(selected_mcqs)}")

        # Step 4: Check if additional MCQs are needed to reach num_mcqs
        if len(final_mcqs) < num_mcqs:
            remaining_mcqs = [mcq for mcq in filtered_mcqs if mcq not in final_mcqs]
            final_mcqs.extend(remaining_mcqs[:num_mcqs - len(final_mcqs)])

        # Step 5: Final count of MCQs from each selection in final_mcqs
        final_mcqs_count_by_selection = {selection: 0 for selection in selections}
        for mcq in final_mcqs:
            for selection_data in selections_data:
                if mcq in MCQ.objects.filter(selection_data['query']):
                    final_mcqs_count_by_selection[selection_data['selection']] += 1

        # Print the count of MCQs from each selection in final_mcqs
        for selection, count in final_mcqs_count_by_selection.items():
            print(f"Final count of MCQs from selection '{selection}': {count}")
        # Step 6: Serialize and prepare data for rendering
        total_time_minutes = time_per_question * len(final_mcqs)
        total_time_seconds = round(total_time_minutes * 60)

        serializer = MCQSerializer(final_mcqs, many=True)
        test_session = TestSession.objects.create(user=user, test_id=test_id, total_questions=len(final_mcqs), selections=selections,totaltime=total_time_seconds)
        current_test=request.user.profile
        current_test.current_test = test_id
        current_test.save()
        for mcq in final_mcqs:
            TestAnswer.objects.create(test_session=test_session, mcq_uid=mcq.uid)
        
        return render(request, 'mcq/mcq.html', {'mcqs': json.dumps(serializer.data), 'count': len(final_mcqs), 'test_id': test_id,'total_time': total_time_minutes})

    else:
        # If cntt_test is not blank, redirect to continue_test 
        # with the existing test ID

        return redirect('cont', test_id=profile.current_test)









@csrf_exempt  
def submit_quiz(request):
    
    if request.method == 'POST':
        mcq_ids = request.POST.getlist('mcq_ids')
        test_id = request.POST.get('test_id')
      
        try:
            test_session = TestSession.objects.get(test_id=test_id, user=request.user)

            # Check if the test has been submitted
            if not test_session.submitted:
                
                # Deny access if the test has not been submitted
                return JsonResponse({'error': 'Test not submitted yet. Access denied.'}, status=403)
       
            if test_session.submitted:
                mcqs = MCQ.objects.filter(uid__in=mcq_ids)
                mcq_data = [{'uid': str(mcq.uid), 'correct_option': mcq.correct_option, 'explanation': mcq.explanation} for mcq in mcqs]
                return JsonResponse(mcq_data, safe=False)
        except ValueError:
            return JsonResponse({'error': 'Invalid UUID'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)



def get_units(request):
    subject_id = request.GET.get('subject_id')
    if not subject_id:
        return JsonResponse({'error': 'subject_id parameter is missing'}, status=400)

    try:
        units = Unit.objects.filter(subject_id=subject_id)
        unit_list = [{'id': str(unit.pk), 'name': unit.name} for unit in units]
        return JsonResponse({'units': unit_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_chapters(request):
    unit_id = request.GET.get('unit_id')
    if not unit_id:
        return JsonResponse({'error': 'unit_id parameter is missing'}, status=400)

    try:
        chapters = Chapter.objects.filter(unit_id=unit_id)
        chapter_list = [{'id': str(chapter.pk), 'name': chapter.name} for chapter in chapters]
        return JsonResponse({'chapters': chapter_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_topics(request):
    chapter_id = request.GET.get('chapter_id')
    if not chapter_id:
        return JsonResponse({'error': 'chapter_id parameter is missing'}, status=400)

    try:
        topics = Topic.objects.filter(chapter_id=chapter_id)
        topic_list = [{'id': str(topic.pk), 'name': topic.name} for topic in topics]
        return JsonResponse({'topics': topic_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def save_answer(request):
    if request.method == 'POST':
        user = request.user
        test_id = request.POST.get('test_id')
        mcq_uid = request.POST.get('mcq_uid')
        selected_option = request.POST.get('selected_option')
        time_spent = request.POST.get('time_spent')
        time_taken = request.POST.get('time_taken')
        minutes, seconds = map(int, time_taken.split(':'))
        total_seconds = minutes * 60 + seconds
        
        try:
            test_session = TestSession.objects.get(user=user, test_id=test_id)
            test_answer = TestAnswer.objects.get(test_session=test_session, mcq_uid=mcq_uid)
            test_answer.timespent = time_spent
            test_session.timetaken = total_seconds
            test_session.save() 
            print(test_session.timetaken)
            if selected_option is not None:  # Check if selected_option is present
                test_answer.selected_option = selected_option
                if selected_option != "":
                    test_answer.is_attempted = True
                else:
                    test_answer.is_attempted = False
            elif time_spent is not None:  # If not, check for time_spent
                test_answer.timespent = time_spent
                
                
                test_answer.save()
            test_answer.save()

            
            test_session.save()
            
            return JsonResponse({'status': 'success'})
        except (TestSession.DoesNotExist, TestAnswer.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Session or Answer not found'}, status=400)
        
from decimal import Decimal


from django.core.exceptions import ObjectDoesNotExist

def continue_test(request, test_id):
    messages.info(request, "You have an ongoing test. Redirecting to continue your previous test.")

    user = request.user

    try:
        test_session = TestSession.objects.get(user=user, test_id=test_id)
    except ObjectDoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Test session not found.'}, status=404)
    
    if test_session.submitted:
        return JsonResponse({'status': 'error', 'message': 'This test has already been submitted.'}, status=400)
    
    # Retrieve test answers in the order they were saved (ordered by id or created_at)
    test_answers = TestAnswer.objects.filter(test_session=test_session).order_by('id')  # You can replace 'id' with 'created_at' if available
    
    mcqs_data = []
    selected_answers = {}
    timespent = {}
    time_taken = getattr(test_session, 'timetaken', 0)  # Defaults to 0 if 'time_taken' attribute is missing
    total_time = test_session.totaltime   # Total allowed time in seconds
    total_time_minutes = total_time/60
# Calculate time left in seconds
    time_left_seconds = total_time - time_taken
    selected_option_texts = {}
# Convert time left into minutes with decimal precision
    time_left_minutes = time_left_seconds / 60
    for index, answer in enumerate(test_answers):
        try:
            mcq = MCQ.objects.get(uid=answer.mcq_uid)
        except ObjectDoesNotExist:
            continue  # Skip if the MCQ does not exist
        if answer.is_attempted:
            selected_option_text = {
                "A": mcq.option_1,
                "B": mcq.option_2,
                "C": mcq.option_3,
                "D": mcq.option_4
            }.get(answer.selected_option)
            
            if selected_option_text:
                selected_option_texts[index] = selected_option_text

    # Populate the selected_answers dictionary
        serializer = MCQSerializer(mcq)
        mcq_data = serializer.data
        mcq_data['selected_option'] = answer.selected_option
        mcq_data['timespent'] = float(answer.timespent)  # Convert Decimal to float for serialization

        mcqs_data.append(mcq_data)

        # Add selected option to selected_answers, default to empty string if not attempted
        selected_answers[index] = answer.selected_option if answer.is_attempted else ''
        timespent[str(mcq.uid)] = float(answer.timespent)  # Convert Decimal to float
    bookmarks = Bookmark.objects.filter(user=user, test_session=test_session)
    bookmarked_mcqs = {}
    for bookmark in bookmarks:
        bookmarked_mcqs[str(bookmark.mcq.uid)] = bookmark.bookmark_type
    mcqs_json = json.dumps(mcqs_data)
    selected_answers_json = json.dumps(selected_answers)
    timespent_json = json.dumps(timespent)
    bookmarked_mcqs_json = json.dumps(bookmarked_mcqs)
    selected_option_texts_json = json.dumps(selected_option_texts)

    return render(request, 'mcq/mcq.html', {
        'mcqs': mcqs_json, 
        'count': len(mcqs_data), 
        'test_id': test_id, 
        'timespent': timespent_json,
        'selected_answers': selected_answers_json,
        'bookmarked_mcqs': bookmarked_mcqs_json,
        'total_time':total_time_minutes ,
        'time_left_minutes':time_left_minutes,
        'selected_option_texts': selected_option_texts_json,
    })


from django.db import transaction

@csrf_exempt
def submitted_active(request):
    
    if request.method == 'POST':
        user = request.user
        user_choices = request.POST.get('userchoices', {})
        print(user_choices)
        test_id = request.POST.get('test_id')
        curr_mcq_uid = request.POST.get('current_que_uid')
        timespent = request.POST.get('timespent')
        timetaken = request.POST.get('timetaken')
        print("time_taken",timetaken)
        minutes, seconds = map(int, timetaken.split(':'))
        total_seconds = minutes * 60 + seconds

        if isinstance(user_choices, str):
            import json
            user_choices = json.loads(user_choices)
        
        score = 0
        total_questions = 0
        correct_answers = {}
        
        
        try:
            with transaction.atomic():
                test_session = TestSession.objects.get(user=user, test_id=test_id)
                test_answer = TestAnswer.objects.get(test_session=test_session, mcq_uid=curr_mcq_uid)
                test_answer.timespent = timespent
                test_answer.save()
                
                print(test_session)
                if not test_session.submitted:

                    for uid, selected_option in user_choices.items():
           
                        mcq = MCQ.objects.get(uid=uid)
                        total_questions += 1
                        correct_answers[uid] = mcq.correct_option
                        test_answer = TestAnswer.objects.get(test_session=test_session, mcq_uid=uid)
                        test_answer.selected_optiontext = selected_option
                        test_answer.save()
                        if mcq.correct_option == selected_option:
                            score += 1
                            
                            test_answer.correct = True
                            
                            test_answer.save()
        
                    response_data = {
                            'score': score,
                            'total_questions': total_questions,
                            'correct_answers': correct_answers,
                        }
                    print(response_data)


                    
                     
                    test_session.timetaken = total_seconds
                    test_session.submitted = True
                    test_session.score = score
                    test_session.save()  # Force update without conditional checks
                    current_test=request.user.profile
                    current_test.current_test = ''
                    current_test.save()
                    
            
                
            return JsonResponse({'status': 'success'})
        except (TestSession.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'You have already submitted the test'}, status=400)

def cont_last_sess(request,email_token):
    user = request.user
    unsubmitted_tests = TestSession.objects.filter(user=user, submitted=False).order_by('-created_at')
    
    return render(request, 'cont_last_sess/cont_sess.html', {'unsubmitted_tests': unsubmitted_tests})




# views.py

from django.shortcuts import render
from django.db.models import Avg, F, Func
from django.db.models.functions import Cast
from django.db.models import UUIDField
from .models import TestSession, TestAnswer, MCQ, difficulties

def analysis_by_difficulty(request,email_token):
    difficulties_list = ['Easy', 'Medium', 'Tough']

    if request.method == 'POST':
        selected_difficulty = request.POST.get('difficulty')
        if selected_difficulty in difficulties_list:
            # Convert mcq_uid to UUID for comparison
            test_answers = TestAnswer.objects.annotate(
                mcq_uid_as_uuid=Cast('mcq_uid', output_field=UUIDField())
            ).filter(
                test_session__user=request.user,
                mcq_uid_as_uuid__in=MCQ.objects.filter(
                    difficulty__name=selected_difficulty
                ).values_list('uid', flat=True)
            )

            total_questions = test_answers.count()
            correct_questions = test_answers.filter(correct=True).count()
            incorrect_questions = total_questions - correct_questions
            average_time = test_answers.aggregate(Avg('timespent'))['timespent__avg']

            test_sessions = TestSession.objects.filter(
                user=request.user,
                test_id__in=test_answers.values_list('test_session__test_id', flat=True)
            )

            test_session_details = []
            for session in test_sessions:
                session_answers = test_answers.filter(test_session=session)
                session_details = {
                    'session': session,
                    'total_questions': session_answers.count(),
                    'correct': session_answers.filter(correct=True).count(),
                    'incorrect': session_answers.filter(correct=False).count(),
                    'average_time': session_answers.aggregate(Avg('timespent'))['timespent__avg']
                }
                test_session_details.append(session_details)

            # Data for the graph
            graph_data = {
                'labels': [str(session.test_id) for session in test_sessions],
                'total_questions': [session_details['total_questions'] for session_details in test_session_details],
                'correct': [session_details['correct'] for session_details in test_session_details],
                'incorrect': [session_details['incorrect'] for session_details in test_session_details],
                'average_time': [session_details['average_time'] for session_details in test_session_details]
            }

            context = {
                'difficulty': selected_difficulty,
                'total_questions': total_questions,
                'correct_questions': correct_questions,
                'incorrect_questions': incorrect_questions,
                'average_time': average_time,
                'test_sessions': test_session_details,
                'graph_data': graph_data
            }
            context.update({'difficulties': difficulties_list})

            return render(request, 'ana/ana.html', context,)

    return render(request, 'ana/ana.html', {'difficulties': difficulties_list})

# views.py
from django.shortcuts import render
from .models import TestSession, TestAnswer
from django.db.models import Avg, Count, Case, When, IntegerField

from decimal import Decimal

def get_accuracy_data():
    # Get all test sessions that are submitted
    test_sessions = TestSession.objects.filter(submitted=True).order_by('created_at')
    total_sessions = len(test_sessions)
    
    # Determine group size based on the number of test sessions
    if total_sessions < 5:
        group_size = 1  # Show individual scores
    elif total_sessions <= 10:
        group_size = 2
    elif total_sessions <= 20:
        group_size = 4
    else:
        group_size = 10

    accuracy_data = []

    # Iterate over test sessions in groups based on the determined group size
    for i in range(0, total_sessions, group_size):
        group = test_sessions[i:i + group_size]
        group_accuracy = Decimal(0)
        total_questions = 0

        for session in group:
            correct_answers = TestAnswer.objects.filter(
                test_session=session,
                correct=True
            ).count()

            total_questions += session.total_questions
            if session.total_questions > 0:
                session_accuracy = (Decimal(correct_answers) / session.total_questions) * 100
                group_accuracy += session_accuracy

        # Calculate average accuracy or individual accuracy for single tests
        if group_size == 1:  # Individual scores
            session = group[0]
            label = f'Test {i + 1}'
            accuracy = float(group_accuracy) if total_questions > 0 else 0
        else:  # Average accuracy for groups
            label = f'Tests {i + 1} - {i + len(group)}'
            accuracy = float(group_accuracy / len(group)) if len(group) > 0 else 0

        # Append data to the list
        accuracy_data.append({
            'label': label,
            'accuracy': accuracy
        })

    return accuracy_data

def accuracy_vs_tests(request, email_token):
    accuracy_data = get_accuracy_data()
    return render(request, 'graph/acc_test.html', {'accuracy_data': accuracy_data})

from django.shortcuts import render
from .models import Subject, MCQ, TestAnswer




from django.shortcuts import render
from .models import Subject, MCQ, TestAnswer, Topic, Unit
import uuid

def analysis_view_sub_acc(request, email_token):
    # Fetch all MCQ UIDs from submitted TestSessions as strings
    submitted_mcq_uids = TestAnswer.objects.filter(
        test_session__submitted=True
    ).values_list('mcq_uid', flat=True).distinct()

    # Fetch MCQs that are associated with these UIDs
    related_mcqs = MCQ.objects.filter(uid__in=submitted_mcq_uids)  # `uid` is string

    # Fetch Topics related to these MCQs
    related_topics = Topic.objects.filter(
        uid__in=related_mcqs.values_list('topic__uid', flat=True)  # `uid` is string
    ).distinct()

    # Fetch Units related to these Topics
    related_units = Unit.objects.filter(
        chapters__topics__in=related_topics
    ).distinct()

    # Fetch Subjects related to these Units
    submitted_subjects = Subject.objects.filter(
        units__in=related_units
    ).distinct()

    labels = [subject.name for subject in submitted_subjects]

    # Prepare data lists
    attempted = []
    correct = []

    for subject in submitted_subjects:
        # Fetch MCQ UIDs related to this subject
        mcq_uids = MCQ.objects.filter(topic__chapter__unit__subject=subject).values_list('uid', flat=True)

        # Total number of attempts for the subject
        attempts_count = TestAnswer.objects.filter(
            mcq_uid__in=mcq_uids,
            test_session__submitted=True
        ).count()

        # Correct answers count
        correct_count = TestAnswer.objects.filter(
            mcq_uid__in=mcq_uids,
            correct=True,
            test_session__submitted=True
        ).count()

        attempted.append(attempts_count)
        correct.append(correct_count)

    context = {
        'labels': labels,
        'attempted': attempted,
        'correct': correct,
    }
    return render(request, 'graph/sub_acc.html', context)



# views.py
from django.shortcuts import render
from .models import TestSession, TestAnswer, MCQ

def get_performance_data():
    # Fetch all submitted test sessions
    test_sessions = TestSession.objects.filter(submitted=True)

    # Prepare a dictionary to store correct and total counts per subject
    subject_performance = {}

    # Iterate through each test session
    for session in test_sessions:
        # Fetch all related test answers
        answers = TestAnswer.objects.filter(test_session=session)

        for answer in answers:
            try:
                # Get the associated MCQ using UUID
                mcq = MCQ.objects.get(uid=answer.mcq_uid)
                subject_name = mcq.topic.chapter.unit.subject.name

                # Initialize counters if not already present
                if subject_name not in subject_performance:
                    subject_performance[subject_name] = {'correct': 0, 'total': 0}

                # Increment total count
                subject_performance[subject_name]['total'] += 1

                # Increment correct count if the answer is correct
                if answer.correct:
                    subject_performance[subject_name]['correct'] += 1

            except MCQ.DoesNotExist:
                # Handle case where MCQ doesn't exist for the UUID
                continue

    # Calculate performance percentage for each subject
    subject_percentage = {
        subject: (data['correct'] / data['total']) * 100
        for subject, data in subject_performance.items()
        if data['total'] > 0
    }

    return subject_percentage

import json

def performance_radar_view(request, email_token):
    performance_data = get_performance_data()
    labels = list(performance_data.keys())
    data = list(performance_data.values())

    context = {
        'labels': json.dumps(labels),  # Convert Python list to JSON
        'data': json.dumps(data),      # Convert Python list to JSON
    }

    return render(request, 'graph/radar.html', context)



from django.shortcuts import render
from .models import TestSession, TestAnswer, MCQ

def get_difficulty_data():
    # Data structure to hold count and total time for each difficulty
    difficulty_data = {
        'Easy': {'total_questions': 0, 'total_time': 0, 'avg_time': 0},
        'Medium': {'total_questions': 0, 'total_time': 0, 'avg_time': 0},
        'Tough': {'total_questions': 0, 'total_time': 0, 'avg_time': 0}
    }

    # Fetch test sessions where submitted=True
    test_sessions = TestSession.objects.filter(submitted=True)

    for session in test_sessions:
        # Fetch all answers for the current session
        test_answers = TestAnswer.objects.filter(test_session=session)
        
        for answer in test_answers:
            try:
                # Fetch the corresponding MCQ using mcq_uid
                mcq = MCQ.objects.get(uid=answer.mcq_uid)
                
                # Get the difficulty level of the MCQ
                difficulty = mcq.difficulty.name  # Assuming 'name' contains 'Easy', 'Medium', 'Tough'
                
                # Update the total count and time spent for the difficulty level
                difficulty_data[difficulty]['total_questions'] += 1
                difficulty_data[difficulty]['total_time'] += answer.timespent

            except MCQ.DoesNotExist:
                print(f"MCQ with ID {answer.mcq_uid} does not exist.")

    # Calculate average time per difficulty
    for difficulty, data in difficulty_data.items():
        if data['total_questions'] > 0:
            data['avg_time'] = data['total_time'] / data['total_questions']

    return difficulty_data

# View to render the HTML page
def difficulty_vs_time_view(request,email_token):
    # Get the difficulty data
    difficulty_data = get_difficulty_data()

    # Prepare context to pass to the template
    context = {
        'difficulty_data': difficulty_data
    }

    # Render the HTML template with the context data
    return render(request, "graph/diff_vs_time.html", context)


from django.shortcuts import render
from .models import TestSession, TestAnswer, MCQ, mcq_types
from django.db.models import Avg, Count
from collections import defaultdict

def type_vs_time(request,email_token):
    # Get all submitted test sessions
    test_sessions = TestSession.objects.filter(submitted=True)

    # Initialize a dictionary to hold the total count of questions and the total time spent per type
    type_data = defaultdict(lambda: {'total_questions': 0, 'total_time': 0})

    # Loop through all test answers in the submitted test sessions
    for session in test_sessions:
        test_answers = TestAnswer.objects.filter(test_session=session)
        for answer in test_answers:
            # Retrieve the related MCQ for the current answer
            mcq = MCQ.objects.filter(uid=answer.mcq_uid).first()
            if mcq and mcq.types:
                mcq_type = mcq.types.types  # Get the type of the question
                # Update the total questions and total time spent on this type
                type_data[mcq_type]['total_questions'] += 1
                type_data[mcq_type]['total_time'] += answer.timespent

    # Prepare the data for the frontend
    labels = []  # Types of questions (e.g., Clinical, Image-Based, General)
    total_questions = []  # Total number of questions for each type
    avg_times = []  # Average time spent on each type (in seconds)

    for mcq_type, data in type_data.items():
        labels.append(mcq_type)
        total_questions.append(data['total_questions'])
        if data['total_questions'] > 0:
            avg_times.append(data['total_time'] / data['total_questions'])  # Calculate average time
        else:
            avg_times.append(0)
    print(avg_times)
    # Prepare the context for the template

    avg_time_st = json.dumps(avg_times, default=decimal_to_json)

    context = {
        'labels': json.dumps(labels),
        'total_questions': json.dumps(total_questions),
        'avg_times': avg_time_st
    }

    # Render the HTML template and pass the context
    return render(request, "graph/type_vs_time.html", context)

def decimal_to_json(obj):
    if isinstance(obj, Decimal):
        return float(obj)  # or str(obj) if you prefer
    raise TypeError("Object of type Decimal is not JSON serializable")



from django.shortcuts import render
from .models import TestSession, TestAnswer, MCQ
from collections import defaultdict

def diff_corr_incorr(request,email_token):
    # Get all the test sessions where submitted=True
    test_sessions = TestSession.objects.filter(submitted=True)

    # Dictionary to track correct and incorrect answers by difficulty level
    difficulty_data = defaultdict(lambda: {'correct': 0, 'incorrect': 0})

    # Loop through each test session
    for session in test_sessions:
        # Get all answers for the current session
        test_answers = TestAnswer.objects.filter(test_session=session)
        
        # Loop through each answer
        for answer in test_answers:
            try:
                # Retrieve the corresponding MCQ using the UUID
                mcq = MCQ.objects.get(pk=answer.mcq_uid)
                difficulty_level = mcq.difficulty.name  # Get difficulty level name

                # Update correct or incorrect count based on the answer's correctness
                if answer.correct:
                    difficulty_data[difficulty_level]['correct'] += 1
                else:
                    difficulty_data[difficulty_level]['incorrect'] += 1
            except MCQ.DoesNotExist:
                # Handle case where the MCQ is missing
                continue

    # Prepare data for frontend (labels and datasets for the chart)
    labels = list(difficulty_data.keys())
    correct_answers = [difficulty_data[difficulty]['correct'] for difficulty in labels]
    incorrect_answers = [difficulty_data[difficulty]['incorrect'] for difficulty in labels]

    # Pass the data to the template
    context = {
        'labels': json.dumps(labels),
        'correct_answers': json.dumps(correct_answers),
        'incorrect_answers': json.dumps(incorrect_answers),
    }

    return render(request, 'graph/diff_corr_incorr.html', context)







from django.shortcuts import render
from .models import TestSession, TestAnswer, MCQ
from collections import defaultdict
import json

def type_corr_incorr(request, email_token):
    # Get all the test sessions where submitted=True
    test_sessions = TestSession.objects.filter(submitted=True,user=request.user)

    # Dictionary to track correct and incorrect answers by MCQ type
    mcq_type_data = defaultdict(lambda: {'correct': 0, 'incorrect': 0})

    # Loop through each test session
    for session in test_sessions:
        # Get all answers for the current session
        test_answers = TestAnswer.objects.filter(test_session=session)

        # Loop through each answer
        for answer in test_answers:
            try:
                # Retrieve the corresponding MCQ using the UUID
                mcq = MCQ.objects.get(pk=answer.mcq_uid)
                
                # Check if mcq.types is not None before accessing its 'types' attribute
                if mcq.types:
                    mcq_type = mcq.types.types  # Get the MCQ type name

                    # Update correct or incorrect count based on the answer's correctness
                    if answer.correct:
                        mcq_type_data[mcq_type]['correct'] += 1
                    else:
                        mcq_type_data[mcq_type]['incorrect'] += 1
                else:
                    # If mcq.types is None, skip this MCQ
                    continue

            except MCQ.DoesNotExist:
                # Handle case where the MCQ is missing
                continue

    # Prepare data for frontend (labels and datasets for the chart)
    labels = list(mcq_type_data.keys())
    correct_answers = [mcq_type_data[mcq_type]['correct'] for mcq_type in labels]
    incorrect_answers = [mcq_type_data[mcq_type]['incorrect'] for mcq_type in labels]

    # Pass the data to the template
    context = {
        'labels': json.dumps(labels),
        'correct_answers': json.dumps(correct_answers),
        'incorrect_answers': json.dumps(incorrect_answers)
    }

    return render(request, 'graph/type_corr_incorr.html', context)

from django.shortcuts import render
from mcqs.models import TestSession
from django.contrib.auth.decorators import login_required

@login_required
def rev_test_home(request, email_token):
    # Fetch all submitted test sessions for the current user and order them by created_at in descending order
    user = request.user
    test_sessions = TestSession.objects.filter(user=user, submitted=True).order_by('-created_at')
    
    # Pass the test_sessions to the template
    return render(request, 'rev_test/rev_test_home.html', {
        'test_sessions': test_sessions
    })




from django.shortcuts import render, get_object_or_404
from mcqs.models import TestSession, TestAnswer, MCQ
from django.contrib.auth.decorators import login_required

@login_required
def test_review(request, email_token):
    # Get the test_id from query parameters
    test_id = request.GET.get('test_id')
    user = request.user
    
    # Fetch the test session based on test_id and user
    test_session = get_object_or_404(TestSession, test_id=test_id, user=user)
    test_session.timetaken_minutes = round(test_session.timetaken / 60, 2)
    # Fetch all test answers related to this session
    test_answers = TestAnswer.objects.filter(test_session=test_session)
    
    # Prepare a list to hold all the MCQ data with answer status
    mcq_data = []
    
    for answer in test_answers:
        # Fetch the MCQ corresponding to this answer
        try:
            mcq = MCQ.objects.get(pk=answer.mcq_uid)
        except MCQ.DoesNotExist:
            continue
        
        # Determine the correct option and if the user's choice is correct
        selected_option = answer.selected_optiontext
        is_correct = answer.correct
        
        # Determine color codes for answers based on the conditions
        options = [
            {
                "text": mcq.option_1,
                "selected": selected_option == mcq.option_1,
                "correct": mcq.correct_option == mcq.option_1,
            },
            {
                "text": mcq.option_2,
                "selected": selected_option == mcq.option_2,
                "correct": mcq.correct_option == mcq.option_2,
            },
            {
                "text": mcq.option_3,
                "selected": selected_option == mcq.option_3,
                "correct": mcq.correct_option == mcq.option_3,
            },
            {
                "text": mcq.option_4,
                "selected": selected_option == mcq.option_4,
                "correct": mcq.correct_option == mcq.option_4,
            },
        ]

        # Append data for each MCQ including the image if present
        mcq_data.append({
            "mcq_uid":mcq.uid,
            "mcq_text": mcq.text,
            "explanation": mcq.explanation,
            "topic": mcq.topic.name,
            "difficulty": mcq.difficulty.name if mcq.difficulty else 'N/A',
            "type": mcq.types.types if mcq.types else 'N/A',
            "time_spent": answer.timespent,
            "options": options,
            "correct": is_correct,
            "is_attempted": answer.is_attempted,
            "image": mcq.image.url if mcq.image else None,  # Pass the image URL if it exists
            "subject": mcq.topic.chapter.unit.subject.name,
            "unit": mcq.topic.chapter.unit.name,
            "chapter": mcq.topic.chapter.name,
        })
        
        connected_users = Connection.objects.filter(
        Q(user=request.user) | Q(connected_user=request.user)  # Either user or connected_user
        ).select_related('user', 'connected_user')

    # Create a unique list of all connected users (excluding the current user)
    connected_users_list = []
    for connection in connected_users:
        if connection.user == request.user:
            connected_users_list.append(connection.connected_user)
        else:
            connected_users_list.append(connection.user)
    # Render the test review template with the retrieved data
    return render(request, 'rev_test/rev_test.html', {
        "test_session": test_session,
        "mcq_data": mcq_data,
        'connected_users': connected_users_list,
    })

def tea(request,email_token):
    return render(request, 'tea/tea_home.html')


def toggle_bookmark(request):
    if request.method == 'POST':
        mcq_uid = request.POST.get('mcq_uid')
        bookmark_type = request.POST.get('bookmark_type')
        test_session_id = request.POST.get('test_session_id')  # Retrieve test session ID from request
        user = request.user

        try:
            mcq = MCQ.objects.get(uid=mcq_uid)
            test_session = TestSession.objects.get(test_id=test_session_id)  # Fetch the test session
        except (MCQ.DoesNotExist, TestSession.DoesNotExist):
            return JsonResponse({'error': 'MCQ or TestSession not found'}, status=404)

        # Check if the bookmark already exists
        bookmark, created = Bookmark.objects.get_or_create(user=user, mcq=mcq, test_session=test_session)

        # Toggle or update bookmark type
        if not created:
            if bookmark.bookmark_type == bookmark_type:
                bookmark.delete()
                return JsonResponse({'status': 'unbookmarked'})
            else:
                bookmark.bookmark_type = bookmark_type
        else:
            # Assign a new unique bkmk_id if a new bookmark is created
            bookmark.bkmk_id = str(uuid.uuid4())
            bookmark.bookmark_type = bookmark_type

        # Save the bookmark
        bookmark.save()

        return JsonResponse({'status': 'bookmarked', 'bookmark_type': bookmark.bookmark_type})

    return JsonResponse({'error': 'Invalid request'}, status=400)


from django.shortcuts import render
from mcqs.models import Bookmark
from hive.models import Connection
from django.db.models import Q  # Import Q for complex queries

def bookmarks_home(request, email_token):
    # Fetch all bookmarks for the current user and include related fields
    star_mcqs = Bookmark.objects.filter(user=request.user, bookmark_type='Star').select_related('mcq', 'test_session')
    unstudied_mcqs = Bookmark.objects.filter(user=request.user, bookmark_type='Unstudied').select_related('mcq', 'test_session')
    other_mcqs = Bookmark.objects.filter(user=request.user, bookmark_type='Other').select_related('mcq', 'test_session')

    # Fetch connections where the user is either 'user' or 'connected_user'
    connected_users = Connection.objects.filter(
        Q(user=request.user) | Q(connected_user=request.user)  # Either user or connected_user
    ).select_related('user', 'connected_user')

    # Create a unique list of all connected users (excluding the current user)
    connected_users_list = []
    for connection in connected_users:
        if connection.user == request.user:
            connected_users_list.append(connection.connected_user)
        else:
            connected_users_list.append(connection.user)

    # Pass the bookmarks categorized by bookmark type and connected users to the template
    context = {
        'star_mcqs': star_mcqs,
        'unstudied_mcqs': unstudied_mcqs,
        'other_mcqs': other_mcqs,
        'connected_users': connected_users_list,  # Add connected users to the context
    }
    
    return render(request, 'bkmk/bkmk.html', context)

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["DELETE"])
def delete_bookmark(request, bkmk_id):
    print("AYAYA")
    try:
        bookmark = Bookmark.objects.get(bkmk_id=bkmk_id, user=request.user)
        bookmark.delete()
        return JsonResponse({'success': True})
    except Bookmark.DoesNotExist:
        return JsonResponse({'error': 'Bookmark not found'}, status=404)

# views.py
from django.http import JsonResponse
from mcqs.models import MCQ
import random

def qod(request):
    try:
        # Get random MCQ
        mcq = MCQ.objects.order_by('?').first()
        
        data = {
            'text': mcq.text,
            'options': [
                mcq.option_1,
                mcq.option_2,
                mcq.option_3,
                mcq.option_4
            ],
            'correct_answer': mcq.correct_option,
            'has_image': bool(mcq.image),
            'image_url': mcq.image.url if mcq.image else None
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({
            'error': 'Failed to fetch question',
            'message': str(e)
        }, status=500)