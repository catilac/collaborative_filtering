"""
prep user-song matrix, and create lists of user_ids and song_ids
"""
import sys
import time

num_songs = num_users = 0
def gen_users_songs_files(filename='train_triplets.txt'):
  print("Reading train data...")
  songs = set()

  start_time = time.time()
  f = open('songs.txt', 'w')

  with open(filename) as file:
    for line in file:
      song_id = line.split('\t')[1]
      if song_id not in songs:
        songs.add(song_id)
        f.write(song_id + '\n')
  
  f.close()
  end_time = time.time()

  num_songs = len(songs)

  print("Done!")
  print("Total songs:", num_songs)
  print("Elapsed Time:", end_time - start_time)

if __name__ == '__main__':
  gen_users_songs_files() 
