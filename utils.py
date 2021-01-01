def list_users(users):
    to_send = ''
    messages = []
    counter = 0
    for user in users:
        if counter == 100:
            messages.append(to_send)
            to_send = ''
            counter = 0
        if user['username']:
            to_send += '<a href="{}">{}</a>'.format('https://t.me/'+user['username'], user['firstname']) + '\n'
        else:
            to_send += user['firstname'] + '\n'
        counter += 1
    if to_send:
        messages.append(to_send)
    return messages

def make_movie_details_message(movie):
    message = '<a href="https://google.com/search?q={}">{}</a>'.format(movie.fullname.replace(' ', '+'), movie.fullname) + '\n'
    if movie.genre: message += movie.genre
    if movie.rating: message += '\n⭐️ ' + movie.rating
    if movie.country: message += '\n🌍 ' + movie.country
    if movie.duration: message += '\n⏳ ' + movie.duration
    if movie.style: message += '\n\n🎭 Style:\n<b>{}</b>'.format(movie.style)
    if movie.plot: message += '\n\n🏷 Categories: \n<b>{}</b>'.format(movie.plot)
    return message

def make_similar_movies_message(movie):
    message = 'If you like <b>"{}"</b>, you might also like these movies (Recommended in order):\n\n'.format(movie.fullname)
    for m in movie.similar_movies:
        if m[1]:
            message += '<a href="https://google.com/search?q={}">{}</a>'.format(m[0].replace(' ', '+'), m[0]) + ' ⭐️ ' + m[1]
        else:
            message += '<a href="https://google.com/search?q={}">{}</a>'.format(m[0].replace(' ', '+'), m[0])
        message += '\n'
    return message