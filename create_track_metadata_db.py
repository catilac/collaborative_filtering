"""
Thierry Bertin-Mahieux (2010) Columbia University
tb2332@columbia.edu

This code creates an SQLite dataset that contains one row
per track and has all the regular metadata.

This is part of the Million Song Dataset project from
LabROSA (Columbia University) and The Echo Nest.


Copyright 2010, Thierry Bertin-Mahieux

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys
import glob
import time
import datetime
import numpy as np
try:
    import sqlite3
except ImportError:
    print 'you need sqlite3 installed to use this program'
    sys.exit(0)


def encode_string(s):
    """
    Simple utility function to make sure a string is proper
    to be used in a SQLite query
    (different than posgtresql, no N to specify unicode)
    EXAMPLE:
      That's my boy! -> 'That''s my boy!'
    """
    return "'" + s.replace("'", "''") + "'"


def create_db(filename):
    """
    Creates the file and an empty table.
    """
    # creates file
    conn = sqlite3.connect(filename)
    # add stuff
    c = conn.cursor()
    q = 'CREATE TABLE songs (track_id text PRIMARY KEY, '
    q += 'title text, song_id text, '
    q += 'artist_name text, '
    q += 'duration real, '
    q += 'artist_hotttnesss real, year int, '
    q += 'time_signature real, time_signature_confidence real, ' 
    q += 'tempo real, danceability real, '
    q += 'key real, key_confidence real, '
    q += 'mode real, mode_confidence real, '
    q += 'start_of_fade_out real, shs_perf int, shs_work int)'
    c.execute(q)
    # commit and close
    conn.commit()
    c.close()
    conn.close()


def q_num_str(val):
  return ", " + str(val) if not np.isnan(val) else ",-1"
 
def fill_from_h5(conn, h5path, verbose=0):
    """
    Add a row with he information from this .h5 file
    Doesn't commit, doesn't close conn at the end!
    """
    h5 = open_h5_file_read(h5path)
    c = conn.cursor()
    # build query
    q = 'INSERT INTO songs VALUES ('
    title = get_title(h5)
    q += ', ' + encode_string(title)
    song_id = get_song_id(h5)
    q += ', ' + encode_string(song_id)
    artist_name = get_artist_name(h5)
    q += ', ' + encode_string(artist_name)
    duration = get_duration(h5)
    q += q_num_str(duration)
    hotttnesss = get_artist_hotttnesss(h5)
    q += q_num_str(hotttnesss)
    year = get_year(h5)
    q += ", " + str(year)
    q += q_num_str(get_time_signature(h5))
    q += q_num_str(get_time_signature_confidence(h5))
    q += q_num_str(get_tempo(h5))
    q += q_num_str(get_danceability(h5))
    q += q_num_str(get_key(h5))
    q += q_num_str(get_key_confidence(h5))
    q += q_num_str(get_mode(h5))
    q += q_num_str(get_mode_confidence(h5))
    q += q_num_str(get_start_of_fade_out(h5))

    # add empty fields for shs perf than work
    q += ", -1, 0"
    # query done, close h5, commit
    h5.close()
    q += ')'
    if verbose > 0:
        print q
    c.execute(q)
    #conn.commit() # we don't take care of the commit!
    c.close()


def add_indices_to_db(conn, verbose=0):
    """
    Since the db is considered final, we can add all sorts of indecies
    to make sure the retrieval time is as fast as possible.
    Indecies take up a little space, but they hurt performance only when
    we modify the data (which should not happen)
    This function commits its changes at the end

    You might want to add your own indices if you do weird query, e.g. on title
    and artist musicbrainz ID.
    Indices should be on the columns of the WHERE of your search, the goal
    is to quickly find the few rows that match the query. The index does not
    care of the field (column) you actually want, finding the row is the
    important step.
    track_id is implicitely indexed as it is the PRIMARY KEY of the table.
    Note: tutorial on MySQL (close enough to SQLite):
    http://www.databasejournal.com/features/mysql/article.php/10897_1382791_1/
                                   Optimizing-MySQL-Queries-and-Indexes.htm
    """
    c = conn.cursor()
    # index to search by (song_id)
    q = "CREATE INDEX idx_song_id ON songs ('song_id')"
    if verbose > 0:
        print q
    c.execute(q)
    conn.commit()


def die_with_usage():
    """ HELP MENU """
    print 'Command to create the track_metadata SQLite database'
    print 'to launch (it might take a while!):'
    print '   python create_track_metadata_db.py [FLAGS] <MSD dir> <tmdb>'
    print 'PARAMS'
    print '   MSD dir   - directory containing .h5 song files in sub dirs'
    print '        tmdb - filename for the database (track_metadata.db)'
    print 'FLAGS'
    print '  -shsdata f  - file containing the SHS dataset'
    print '                (you can simply concatenate train and test)'
    print '  -verbose    - print every query'
    sys.exit(0)


if __name__ == '__main__':

    # help menu
    if len(sys.argv) < 3:
        die_with_usage()

    # import HDF5 stuff
    # yes, it is worth of a WTF like this last one:
    # http://thedailywtf.com/
    #   Articles/CompareObjectAsIAlertDocumentOrNullIfNotCastable-and-More.aspx
    # but I plan to buy some bad code offsets anyway
    # http://codeoffsets.com/
    pythonsrc = os.path.join(sys.argv[0], '../../../PythonSrc')
    pythonsrc = os.path.abspath(pythonsrc)
    sys.path.append(pythonsrc)
    from hdf5_getters import *

    verbose = 0
    shsdataset = ''
    while True:
        if sys.argv[1] == '-verbose':
            verbose = 1
        elif sys.argv[1] == '-shsdata':
            shsdataset = sys.argv[2]
            sys.argv.pop(1)
        else:
            break
        sys.argv.pop(1)

    # read params
    maindir = os.path.abspath(sys.argv[1])
    dbfile = os.path.abspath(sys.argv[2])

    # sanity checks
    if not os.path.isdir(maindir):
        print 'ERROR: %s is not a directory.' % maindir
    if os.path.exists(dbfile):
        print 'ERROR: %s already exists! delete or provide a new name' % dbfile
        sys.exit(0)
    if shsdataset != '' and not os.path.isfile(shsdataset):
        print 'ERROR %s does not exist.' % shsdataset
        sys.exit(0)

    # start time
    t1 = time.time()

    # create dataset
    create_db(dbfile)

    # open connection
    conn = sqlite3.connect(dbfile)

    # iterate HDF5 files
    cnt_files = 0
    for root, dirs, files in os.walk(maindir):
        files = glob.glob(os.path.join(root, '*.h5'))
        for f in files:
            fill_from_h5(conn, f, verbose=verbose)
            cnt_files += 1
            if cnt_files % 200 == 0:
                conn.commit() # we commit only every 200 files!
    conn.commit()
    t2 = time.time()
    stimelength = str(datetime.timedelta(seconds=t2 - t1))
    print 'added the content of', cnt_files, 'files to database:', dbfile
    print 'it took:', stimelength

    # add SHS data
    if shsdataset != '':
        print 'We add SHS data from file: %s' % shsdataset
        # iterate over SHS file
        shs = open(shsdataset, 'r')
        for line in shs:
            if line == '' or line.strip() == '':
                continue
            if line[0] == '#':
                continue
            # work
            if line[0] == '%':
                works = map(lambda w: int(w),
                            line[1:].split(' ')[0].split(',')[:-1])
                work = min(works)
                continue
            # regular line
            tid, aid, perf = line.strip().split('<SEP>')
            q = "UPDATE songs SET shs_perf=" + perf + ", shs_work=" + str(work)
            q += " WHERE track_id='" + tid + "'"
            if verbose > 0:
                print q
            conn.execute(q)
        # iteration done
        shs.close()
        conn.commit()

    # add indices
    c = conn.cursor()
    res = c.execute('SELECT Count(*) FROM songs')
    nrows_before = res.fetchall()[0][0]
    add_indices_to_db(conn, verbose=verbose)
    res = c.execute('SELECT Count(*) FROM songs')
    nrows_after = res.fetchall()[0][0]
    c.close()
    # sanity check
    assert nrows_before == nrows_after, 'Lost rows during indexing?'
    if nrows_before != 1000000:
        print '*********************************************************'
        print 'We got', nrows_before, 'rows.'
        print 'This is not the full MillionSongDataset! just checking...'
        print '*********************************************************'

    # close connection
    conn.close()

    # end time
    t3 = time.time()

    # DONE
    print 'done! (indices included) database:', dbfile
    stimelength = str(datetime.timedelta(seconds=t3 - t1))
    print 'execution time:', stimelength
