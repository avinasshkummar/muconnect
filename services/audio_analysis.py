from werkzeug.utils import secure_filename
import tempfile
import os
import filetype
import whisper
from pydub import AudioSegment
import psycopg2
from db import get_db_connection  # Import the function from db.py
from textblob import TextBlob
from txtai.pipeline import Summary
from keybert import KeyBERT


class AudioAnalyzer:
    def __init__(self, audio_file):
        self.audio_file = audio_file
    def analyse_audio(self, applicant_id):
        # save the audio file to a desired location
        # if folder doesn't exist, create it
        # take a temp path if upload_folder is not set
        filename = secure_filename(self.audio_file.filename)
        upload_folder = tempfile.gettempdir()
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        self.audio_file.save(os.path.join(upload_folder, filename))

        # check audio format
        audio_path = os.path.join(upload_folder, filename)
        audio_type = filetype.guess(audio_path)
        if audio_type is None:
            return {'status': 'error', 'message': 'Unable to determine audio format'}
        try:
            audio_format = audio_type.extension
            if audio_format != 'mp3':
                #audio path without extension
                new_audio_path = audio_path.split('.')[0] + ".mp3"
                if os.path.exists(new_audio_path):
                    os.remove(new_audio_path)
                command = "ffmpeg -i " + audio_path + " " + new_audio_path
                os.system(command)
                audio_path = new_audio_path
                audio_format = 'mp3'
            # call the speech to text api
                
            model = whisper.load_model("medium")
            # Load audio file
            audio = AudioSegment.from_file(audio_path)

            # Length of audio in milliseconds
            audio_length = len(audio)

            # Initialize start and end times
            start_time = 0
            end_time = 10000  # 10 seconds in milliseconds

            # Initialize transcription
            transcription = ""

            while start_time < audio_length:
                # Extract 10-second chunk
                chunk = audio[start_time:end_time]

                # Save chunk to temporary file
                temp_file = "temp.mp3"
                chunk.export(temp_file, format="mp3")

                # Load chunk and pad/trim it to fit 10 seconds
                chunk_audio = whisper.load_audio(temp_file)
                chunk_audio = whisper.pad_or_trim(chunk_audio)

                # Make log-Mel spectrogram and move to the same device as the model
                mel = whisper.log_mel_spectrogram(chunk_audio).to(model.device)

                # detect the spoken language
                _, probs = model.detect_language(mel)
                print(f"Detected language: {max(probs, key=probs.get)}")

                # decode the audio
                options = whisper.DecodingOptions(fp16 = False)
                result = whisper.decode(model, mel, options)
                # Delete temporary file
                os.remove(temp_file)

                transcription += result.text + " "
                # Move to next chunk
                start_time = end_time
                end_time += 10000

            # Print final transcription
            print(transcription)

            # Insert the transcription into the Audios_analysis table
            summary = Summary('sshleifer/distilbart-cnn-12-6')
            summary_text = summary(transcription, maxlength=100)
            print(summary_text)
            blob = TextBlob(transcription)
            sentiment = blob.sentiment.polarity
            kw_model = KeyBERT()
            keywords = kw_model.extract_keywords(transcription, keyphrase_ngram_range=(1, 1), stop_words=None)

            # Get only the keywords, not the scores
            keys = [keyword[0] for keyword in keywords]

            print(keys)

            transcription_data = {
                        'applicant_id': applicant_id,
                        'transcription': transcription,
                        'sentiment_analysis': sentiment,
                        'summarization': summary_text,
                    }
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute("INSERT INTO Audios_analysis (applicant_id, audio_transcription, sentiment_analysis, summarization) VALUES (%(applicant_id)s, %(transcription)s, %(sentiment_analysis)s, %(summarization)s)", transcription_data)
            
            tag_ids=[]
            for keyword in keys:
                cur.execute("INSERT INTO Tags (tag) VALUES (%s) ON CONFLICT (tag) DO NOTHING RETURNING id", (keyword,))
                
                tag_id = cur.fetchone()
                if tag_id is not None:
                    tag_ids.append(tag_id[0])

            # Insert relationships into Relationship_tag_to_audio table
            for tag_id in tag_ids:
                cur.execute("INSERT INTO Relationship_tag_to_audio (audio_id, tag_id) VALUES (%s, %s)", (applicant_id, tag_id))
            conn.commit()
            cur.close()
            conn.close()
            return {'status': 'success'}
        except Exception as e:
            print(str(e))
            return {'status': 'failure'}
