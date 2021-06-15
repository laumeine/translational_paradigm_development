# 3 files are output:

# detailed coordinates (.csv)
- 'subject_ID'
- 'condition': EC/YC/CC
- 'block': integer, ascending from 1 to BLOCKS
- 'trial': integer, ascending from 1 to TRIALS_PER_BLOCK
- 'phase': number of phase
- 'name': name of phase
- 'x': x coordinate
- 'y': y coordinate
- 'goal': Did the subject reach a safe space? (True/False)
- 'move': number of moves (cumulative)
- 'rt': reaction time (s)
- 'SP_1x': safe space 1 x coordinate
- 'SP_1y': safe space 1 y coordinate
- 'SP_2x': safe space 2 x coordinate
- 'SP_2y': safe space 2 y coordinate
- 'SP_3x': safe space 3 x coordinate
- 'SP_3y': safe space 3 y coordinate
- 'SP_4x': safe space 4 x coordinate
- 'SP_4y': safe space 4 y coordinate


# durations per phase(.csv)
- 'block': integer, ascending from 1 to BLOCKS
- 'trial': integer, ascending from 1 to TRIALS_PER_BLOCK
- 'phase': number of phase
- 'duration': duration of phase (s)


# stimulus aversiveness rating (.txt)