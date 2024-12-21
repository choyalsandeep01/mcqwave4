from django.shortcuts import render
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ConnectionRequest, Connection

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q  # Import Q for complex queries
from .models import ConnectionRequest, Connection  # Import your models

@login_required
def hive_home(request, email_token):
    # Get the current user
    user = request.user

    # Fetch connected users in both directions
    connections = Connection.objects.filter(
        Q(user=user) | Q(connected_user=user)  # Use Q for OR queries
    ).select_related('user', 'connected_user')

    # Fetch pending connection requests
    pending_requests = ConnectionRequest.objects.filter(to_user=user)

    # Prepare the list of connected users, handling both directions
    connected_users = []
    for connection in connections:
        if connection.user == user:
            connected_users.append(connection.connected_user)
        else:
            connected_users.append(connection.user)

    # Render the HIVE home template
    context = {
        'connected_users': connected_users,  # Updated variable name
        'pending_requests': pending_requests
    }
    return render(request, 'hive/hive_home.html', context)


from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import Connection, ConnectionRequest
import json

def send_connection_request(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')

        # Check if the username provided is the same as the logged-in user
        if username == request.user.username:
            return JsonResponse({'error': 'You cannot send a connection request to yourself.'}, status=400)

        try:
            # Check if the user exists
            to_user = User.objects.get(username=username)

            # Check if the users are already connected
            if Connection.objects.filter(user=request.user, connected_user=to_user).exists() or \
               Connection.objects.filter(user=to_user, connected_user=request.user).exists():
                return JsonResponse({'error': 'You are already connected with this user.'}, status=400)

            # Check if the current user has already received a request from the target user
            if ConnectionRequest.objects.filter(from_user=to_user, to_user=request.user).exists():
                return JsonResponse({'error': f'You have already received a connection request from {username}.'}, status=400)

            # Check if the current user has already sent a request to the target user
            if ConnectionRequest.objects.filter(from_user=request.user, to_user=to_user).exists():
                return JsonResponse({'error': 'You have already sent a connection request to this user.'}, status=400)

            # Create a new connection request if no issues
            ConnectionRequest.objects.create(from_user=request.user, to_user=to_user)

            return JsonResponse({'success': True})
        
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found.'}, status=404)

    return JsonResponse({'error': 'Invalid request.'}, status=400)



from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import ConnectionRequest, Connection, User
import json

@login_required
def handle_connection_request(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        from_username = data.get('from_username')
        action = data.get('action')  # Either 'accept' or 'decline'

        try:
            # Get the user who sent the request
            from_user = User.objects.get(username=from_username)
            # Check if there is a pending connection request
            connection_request = ConnectionRequest.objects.get(from_user=from_user, to_user=request.user)

            if action == 'accept':
                # Add the connection and remove the request
                Connection.objects.create(user=request.user, connected_user=from_user)
                connection_request.delete()  # Remove from pending requests
                return JsonResponse({'success': True, 'message': 'Connection accepted.'})

            elif action == 'decline':
                # Remove the request without creating a connection
                connection_request.delete()
                return JsonResponse({'success': True, 'message': 'Connection request declined.'})

        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found.'}, status=404)
        except ConnectionRequest.DoesNotExist:
            return JsonResponse({'error': 'Connection request not found.'}, status=404)

    return JsonResponse({'error': 'Invalid request.'}, status=400)




import json
import uuid
from django.http import JsonResponse
from django.contrib.auth.models import User
from mcqs.models import MCQ  # Ensure your MCQ model is imported
from .models import Shared_Bookmark  # Ensure your Shared_Bookmark model is imported

def share_bookmark(request, bookmark_id):
    print(bookmark_id)
    if request.method == 'POST':
        try:
            # Validate if the bookmark_id is a valid UUID
            try:
                bookmark_id = uuid.UUID(bookmark_id)  # Check if it's a valid UUID
            except ValueError:
                return JsonResponse({'error': 'Invalid bookmark ID. It must be a valid UUID.'}, status=400)

            # Parse the JSON data from the request body
            data = json.loads(request.body)
            user_ids = data.get('users', [])
            print(user_ids)
            # Get the current user (sender)
            sender = request.user

            # Check if the MCQ exists (using the UID)
            try:
                mcq = MCQ.objects.get(uid=bookmark_id)  # Assuming your MCQ model has a uid field
            except MCQ.DoesNotExist:
                return JsonResponse({'error': 'MCQ not found'}, status=404)

            # Initialize a list to store existing shared records
            existing_shares = []

            # Loop through the selected users and create Shared_Bookmark records
            for user_id in user_ids:
                try:
                    recipient = User.objects.get(id=user_id)

                    # Check if the MCQ has already been shared between the sender and recipient in either direction
                    existing_shared = Shared_Bookmark.objects.filter(
                        mcq=mcq,
                        sender__in=[sender, recipient],
                        recipient__in=[sender, recipient]
                    ).first()

                    if existing_shared:
                        # If it exists, store the recipient's username and shared time
                        shared_time = existing_shared.shared_at.strftime('%d-%m-%Y %I:%M:%S %p')  # Format to include AM/PM
                        existing_shares.append({
                            'username': recipient.username,
                            'shared_at': shared_time
                        })
                        continue  # Skip to the next user

                    # Generate a unique UUID for sb_uid
                    sb_uid = str(uuid.uuid4())  # Generate a new UUID

                    # Create a Shared_Bookmark entry
                    Shared_Bookmark.objects.create(
                        sb_uid=sb_uid,  # Use the generated UUID
                        mcq=mcq,  # Store the actual MCQ object
                        sender=sender,
                        recipient=recipient
                    )
                except User.DoesNotExist:
                    return JsonResponse({'error': f'User with ID {user_id} not found'}, status=400)

            # If there are existing shares, format the message
            if existing_shares:
                existing_users = ', '.join(
                    f"{share['username']} (shared at {share['shared_at']})" for share in existing_shares
                )
                return JsonResponse({
                    'error': f'This MCQ has already been shared with: {existing_users}.',
                }, status=400)

            return JsonResponse({'message': 'Bookmark shared successfully!'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid data format'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .models import Shared_Test, TestSession
from mcqs.models import TestSession
import json

@csrf_exempt  # For simplicity in development, but use CSRF tokens properly in production
def share_test(request, test_id):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request
            data = json.loads(request.body)
            user_ids = data.get('users', [])

            if not user_ids:
                return JsonResponse({'error': 'No users selected'}, status=400)

            # Get the test session
            try:
                test_session = TestSession.objects.get(test_id=test_id)
            except TestSession.DoesNotExist:
                return JsonResponse({'error': 'Test session not found'}, status=404)

            # Get the sender (the current authenticated user)
            sender = request.user

            already_shared_users = []
            newly_shared_users = []

            # Iterate over the selected user IDs and create shared test records
            for user_id in user_ids:
                try:
                    recipient = User.objects.get(id=user_id)

                    # Check if the test session is already shared with the user
                    if Shared_Test.objects.filter(test_session=test_session, sender=sender, recipient=recipient).exists():
                        already_shared_users.append(recipient.username)
                    else:
                        # Create a new shared test record if it doesn't exist
                        st_uid = str(uuid.uuid4())
                        Shared_Test.objects.create(
                            st_uid=st_uid,
                            test_session=test_session,
                            sender=sender,
                            recipient=recipient,
                        )
                        newly_shared_users.append(recipient.username)
                except User.DoesNotExist:
                    continue  # Skip if a user ID is invalid

            # Prepare response messages
            if already_shared_users and newly_shared_users:
                return JsonResponse({
                    'message': f"Test session shared successfully with: {', '.join(newly_shared_users)}. Already shared with: {', '.join(already_shared_users)}"
                }, status=200)
            elif already_shared_users:
                return JsonResponse({
                    'message': f"Test session has already been shared with: {', '.join(already_shared_users)}"
                }, status=200)
            elif newly_shared_users:
                return JsonResponse({
                    'message': f"Test session shared successfully with: {', '.join(newly_shared_users)}"
                }, status=200)

            return JsonResponse({'error': 'No valid users to share with'}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from itertools import chain
from operator import attrgetter
from .models import Shared_Bookmark, Shared_Test, Connection
from mcqs.models import MCQ
from mcqs.models import TestSession  # Assuming you have a TestSession model

def shared(request, userId):
    connected_user = get_object_or_404(User, id=userId)

    # Check if a connection exists
    connection_exists = Connection.objects.filter(
        Q(user=request.user, connected_user=connected_user) |
        Q(user=connected_user, connected_user=request.user)
    ).exists()

    if not connection_exists:
        return render(request, 'hive/error.html', {'message': 'You are not connected to this user.'})

    # Fetch shared MCQs
    shared_mcqs = Shared_Bookmark.objects.filter(
        Q(sender=request.user, recipient=connected_user) |
        Q(sender=connected_user, recipient=request.user)
    )

    # Fetch shared Test Sessions
    shared_tests = Shared_Test.objects.filter(
        Q(sender=request.user, recipient=connected_user) |
        Q(sender=connected_user, recipient=request.user)
    )

    # Combine and sort the shared items by 'shared_at'
    shared_items = sorted(
        chain(shared_mcqs, shared_tests),
        key=attrgetter('shared_at')
    )

    items = []
    for shared_item in shared_items:
        if isinstance(shared_item, Shared_Bookmark):
            # Fetch detailed MCQ data
            mcq = MCQ.objects.get(uid=shared_item.mcq.uid)
            items.append({
                'type': 'mcq',
                'data': {
                    'id': mcq.uid,
                    'text': mcq.text,
                    'image': mcq.image.url if mcq.image else None,
                    'options': [mcq.option_1, mcq.option_2, mcq.option_3, mcq.option_4],
                    'correct_option': mcq.correct_option,
                    'explanation': mcq.explanation,
                    'difficulty': mcq.difficulty.name if mcq.difficulty else 'N/A',
                    'type': mcq.types.types if mcq.types else 'N/A',
                    'hierarchy': f"{mcq.topic.chapter.unit.subject.name} > {mcq.topic.chapter.unit.name} > {mcq.topic.chapter.name} > {mcq.topic.name}",
                    'shared_by': 'me' if shared_item.sender == request.user else connected_user.username,
                    'shared_at': shared_item.shared_at
                }
            })
        elif isinstance(shared_item, Shared_Test):
            # Prepare test session data, only showing the test_id
            items.append({
                'type': 'test_session',
                'data': {
                    'test_id': shared_item.test_session.test_id,  # Show only test_id
                    'shared_by': 'me' if shared_item.sender == request.user else connected_user.username,
                    'shared_at': shared_item.shared_at
                }
            })

    return render(request, 'hive/hive_share.html', {
        'connected_user': connected_user,
        'items': items
    })
