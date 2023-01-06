import os
from keep_alive import keep_alive

keep_alive()
"""
Basic example for a bot that works with polls. Only 3 people are allowed to interact with each
poll/quiz the bot generates. The preview command generates a closed poll/quiz, exactly like the
one the user sends the bot
"""
import logging
import os

from telegram import (
    KeyboardButton,
    KeyboardButtonPollType,
    Poll,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)

from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PollAnswerHandler,
    PollHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    filename='Bot.txt',
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inform user about what this bot can do"""
    await update.message.reply_text(
        "Please select /poll to get a Poll, /quiz to get a Quiz or /preview"
        " to generate a preview for your poll")


async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a predefined poll"""
    questions = [
        "1 minute", "10 minutes", "30 minutes", "One Hour", "1 Day", "Custom"
    ]
    message = await context.bot.send_poll(
        update.effective_chat.id,
        "When would you like to be reminded?",
        questions,
        explanation="Please select a proper answer for the poll",
        is_anonymous=False,
        allows_multiple_answers=True,
    )
    logging.info(" %s is the message ", message)
    # Save some info about the poll the bot_data for later use in receive_poll_answer
    payload = {
        message.poll.id: {
            "questions": questions,
            "message_id": message.message_id,
            "chat_id": update.effective_chat.id,
            "answers": 0,
        }
    }
    logging.info(" %s is the payload", payload)
    context.bot_data.update(payload)


async def receive_poll_answer(update: Update,
                              context: ContextTypes.DEFAULT_TYPE) -> None:
    """Summarize a users poll vote"""
    answer = update.poll_answer
    answered_poll = context.bot_data[answer.poll_id]
    try:
        questions = answered_poll["questions"]
    # this means this poll answer update is from an old poll, we can't do our answering then
    except KeyError:
        logging.exception("no key named 'questions' in answered_poll",
                          exc_info=True)
        return
    selected_options = answer.option_ids
    logging.info("the selected options are %s", selected_options)
    answer_string = ""
    answer_string = f"Sure! will remind you in {questions[selected_options[0]]}"
    # for question_id in selected_options:
    #     if question_id != selected_options[-1]:
    #         answer_string += questions[question_id] + " and "
    #     else:
    #         answer_string += questions[question_id]
    logging.info("is the answer string %s", answer_string)
    await context.bot.send_message(
        chat_id=answered_poll["chat_id"],
        text=answer_string,
    )

    answered_poll["answers"] += 1
    # Close poll after one participant voted
    if answered_poll["answers"] == 1:
        logging.info("Participant has voted for : %s", answer)
        await context.bot.stop_poll(answered_poll["chat_id"],
                                    answered_poll["message_id"])


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a predefined poll"""
    questions = ["1", "2", "4", "20"]
    message = await update.effective_message.reply_poll(
        "How many eggs do you need for a cake?",
        questions,
        type=Poll.QUIZ,
        correct_option_id=2)
    # Save some info about the poll the bot_data for later use in receive_quiz_answer
    payload = {
        message.poll.id: {
            "chat_id": update.effective_chat.id,
            "message_id": message.message_id
        }
    }
    context.bot_data.update(payload)


async def receive_quiz_answer(update: Update,
                              context: ContextTypes.DEFAULT_TYPE) -> None:
    """Close quiz after three participants took it"""
    # the bot can receive closed poll updates we don't care about
    if update.poll.is_closed:
        return
    if update.poll.total_voter_count == 3:
        try:
            quiz_data = context.bot_data[update.poll.id]
        # this means this poll answer update is from an old poll, we can't stop it then
        except KeyError:
            return
        await context.bot.stop_poll(quiz_data["chat_id"],
                                    quiz_data["message_id"])


async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask user to create a poll and display a preview of it"""
    # using this without a type lets the user chooses what he wants (quiz or poll)
    button = [[
        KeyboardButton("Press me!", request_poll=KeyboardButtonPollType())
    ]]
    message = "Press the button to let the bot generate a preview for your poll"
    # using one_time_keyboard to hide the keyboard
    await update.effective_message.reply_text(message,
                                              reply_markup=ReplyKeyboardMarkup(
                                                  button,
                                                  one_time_keyboard=True))


async def receive_poll(update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> None:
    """On receiving polls, reply to it by a closed poll copying the received poll"""
    actual_poll = update.effective_message.poll
    # Only need to set the question and options, since all other parameters don't matter for
    # a closed poll
    await update.effective_message.reply_poll(
        question=actual_poll.question,
        options=[o.text for o in actual_poll.options],
        # with is_closed true, the poll/quiz is immediately closed
        is_closed=True,
        reply_markup=ReplyKeyboardRemove(),
    )


async def help_handler(update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display a help message"""
    await update.message.reply_text(
        "Use /quiz, /poll or /preview to test this bot.")


def main() -> None:
    """Run bot."""
    # Create the Application and pass it your bot's token.
    print(os.getenv("TOKEN"), "is the token")
    application = Application.builder().token(os.environ.get("TOKEN")).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("poll", poll))
    application.add_handler(CommandHandler("quiz", quiz))
    application.add_handler(CommandHandler("preview", preview))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(MessageHandler(filters.POLL, receive_poll))
    application.add_handler(PollAnswerHandler(receive_poll_answer))
    application.add_handler(PollHandler(receive_quiz_answer))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if True:
    main()
