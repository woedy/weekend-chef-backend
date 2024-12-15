from pusher import Pusher
from django.shortcuts import render

from bookednise_pro import settings
from django.http import HttpResponse



def send_message(channel, event, message):
    pusher = Pusher(
        app_id=settings.PUSHER_APP_ID, 
        key=settings.PUSHER_KEY, 
        secret=settings.PUSHER_SECRET, 
        cluster=settings.PUSHER_CLUSTER,
        ssl=settings.PUSHER_SSL
        )
    
    pusher.trigger(channel, event, message)


def send_chat_message(request):
    # Process the message
    #message = request.POST.get('message')
    message = "Hellooo Sama"

    # Trigger the event
    send_message('chat-channel', 'new-message', {'message': message})
    return render(request, 'chat.html')



