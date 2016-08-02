import csv
import time
from scipy import sparse, io

def get_data_dict():
  data = {}
  print("Loading Data...")
  t0 = time.time()
  with open('train_triplets.txt') as file:
    csv_reader = csv.reader(file, delimiter='\t')
    for row in csv_reader:
      user_id, song_id, play_count = row
      if user_id not in data:
        data[user_id] = {song_id: play_count}
      else:
        data[user_id][song_id] = play_count
  print("Done! After:", time.time() - t0)
  return data

def create_index(filename):
  idx = 0
  index_dict = {}
  with open(filename) as file:
    for line in file:
      index_dict[line.rstrip()] = idx
      idx += 1
  return index_dict

def create_sparse_matrix():
  user_play_counts = get_data_dict()

  print("Building indexes...")
  t0 = time.time()
  user_idx = create_index('small_users.txt')
  song_idx = create_index('small_songs.txt')
  print("Done! After:", time.time() - t0)

  print("Forming data matrices...")
  t0 = time.time()
  row = []
  col = []
  data = []
  for user, ratings in user_play_counts.items():
    if user not in user_idx:
      continue
    row_idx = user_idx[user]
    for song, count in ratings.items():
      if song not in song_idx:
        continue
      row.append(row_idx)
      col.append(song_idx[song])
      data.append(int(count))
  print("Done! After:", time.time() - t0)


  print("Creating COO mat")
  t0 = time.time()
  num_users = len(user_idx)
  num_songs = len(song_idx)
  mat = sparse.coo_matrix((data, (row, col)), shape=(num_users, num_songs))
  print("Done! After:", time.time() - t0)

  # Clean up
  del(user_play_counts)
  del(user_idx)
  del(song_idx)
  del(data)
  print("Writing out...")
  t0 = time.time()
  io.mmwrite('small_r.mtx', mat, field='integer')
  print("Done! After:", time.time() - t0)



if __name__ == '__main__':
  create_sparse_matrix()

         
