#!/usr/bin/python3
import random
from music21 import *

# --- 1. CONFIGURATION ---

# Standard Guitar Tuning: E2, A2, D3, G3, B3, e4
TUNING = [40, 45, 50, 55, 59, 64] 
NUM_STRINGS = 6
MAX_FRET = 15
MELODY_LENGTH = 30  # Number of notes to compose

# Genetic Algorithm Parameters
POPULATION_SIZE = 100
MUTATION_RATE = 0.1
NUM_GENERATIONS = 200

# Rhythm options (Genetic Algorithm only optimizes pitch, rhythm is random here)
NOTE_DURATIONS = [0.5, 1.0] 

# Reference Scale: C Major
# 0=C, 2=D, 4=E, 5=F, 7=G, 9=A, 11=B
SCALE_C_MAJOR = [0, 2, 4, 5, 7, 9, 11]

# --- 2. GENERATION ---

def generate_random_gene():
    """Generates a random position (String Index, Fret Number)."""
    s = random.randint(0, NUM_STRINGS - 1)
    f = random.randint(0, MAX_FRET)
    return (s, f)

def generate_individual():
    """Creates a complete random melody (a list of genes)."""
    return [generate_random_gene() for _ in range(MELODY_LENGTH)]

# --- 3. FITNESS FUNCTION (Musicality + Technique) ---

def get_note_midi(string_idx, fret):
    """Calculates the MIDI note value based on string and fret."""
    return TUNING[string_idx] + fret

def fitness_function(chromosome):
    """
    Evaluates how 'good' a melody is based on:
    1. Harmony (Is it in C Major?)
    2. Playability (Are the jumps between notes physically possible?)
    3. Melodic contour (Are the intervals pleasing?)
    """
    score = 0
    
    # Pre-calculate MIDI values for the whole melody
    midi_notes = [get_note_midi(s, f) for s, f in chromosome]
    
    for i in range(len(chromosome)):
        current_midi = midi_notes[i]
        string_idx, fret = chromosome[i]
        
        # --- CRITERION 1: MUSICALITY (Harmony) ---
        # Get the pitch class (0-11)
        chroma = current_midi % 12 
        
        if chroma in SCALE_C_MAJOR:
            score += 10  # Reward: Note is in key
            
            # Extra bonus for Tonic (C) or Dominant (G)
            if chroma == 0 or chroma == 7: 
                score += 5
        else:
            score -= 50  # Severe Penalty: Note is out of key (dissonant)

        # --- CRITERION 2: TECHNIQUE (Playability) ---
        if i > 0:
            prev_string, prev_fret = chromosome[i-1]
            prev_midi = midi_notes[i-1]
            
            # Calculate physical distance on the fretboard
            fret_dist = abs(fret - prev_fret)
            string_dist = abs(string_idx - prev_string)
            
            # Penalize large physical jumps for the hand
            score -= (fret_dist * 2) + (string_dist * 5)
            
            # --- CRITERION 3: MELODY (Intervals) ---
            # Penalize pitch jumps larger than an octave (12 semitones)
            interval = abs(current_midi - prev_midi)
            if interval > 12: 
                score -= 20 # Jump is too wide
            elif interval == 0:
                score -= 5  # Boring: Same note repeated immediately
    
    # Final Bonus: The melody should resolve to the Tonic (C)
    last_note_chroma = midi_notes[-1] % 12
    if last_note_chroma == 0: # C
        score += 30

    return score

# --- 4. GENETIC ALGORITHM CORE ---

def crossover(p1, p2):
    """Single-point crossover: combines two parents to make a child."""
    split = random.randint(1, len(p1) - 1)
    return p1[:split] + p2[split:]

def mutate(chromosome):
    """Mutation: Randomly changes one note in the melody."""
    mutant = list(chromosome) 
    if random.random() < MUTATION_RATE:
        idx = random.randint(0, len(mutant) - 1)
        mutant[idx] = generate_random_gene()
    return mutant

def genetic_algorithm():
    population = [generate_individual() for _ in range(POPULATION_SIZE)]
    
    for gen in range(NUM_GENERATIONS):
        # Evaluate population
        scored_pop = [(ind, fitness_function(ind)) for ind in population]
        # Sort by score (Highest first)
        scored_pop.sort(key=lambda x: x[1], reverse=True)
        
        # Logging
        if gen % 50 == 0:
            print(f"Gen {gen}: Best Score = {scored_pop[0][1]}")
            
        # Selection (Select top 30%)
        top_performers = [x[0] for x in scored_pop[:int(POPULATION_SIZE * 0.3)]]
        
        # --- NEW GENERATION ---
        new_pop = []
        
        # Elitism: Automatically keep the absolute best solution from previous gen
        new_pop.append(top_performers[0])
        
        # Fill the rest of the population with children
        while len(new_pop) < POPULATION_SIZE:
            parent1 = random.choice(top_performers)
            parent2 = random.choice(top_performers)
            child = mutate(crossover(parent1, parent2))
            new_pop.append(child)
            
        population = new_pop
        
    return max(population, key=fitness_function)

# --- 5. VISUALIZATION AND PLAYBACK ---

def play_and_show(chromosome):
    s = stream.Score()
    p = stream.Part()
    p.insert(0, instrument.AcousticGuitar())
    p.insert(0, tempo.MetronomeMark(number=120))
    
    print("\n--- GENERATED MELODY (Tablature) ---")
    # Standard ASCII Tab lines
    visual_lines = ["e|", "B|", "G|", "D|", "A|", "E|"]
    
    for s_idx, fret in chromosome:
        # Music21 Note Construction
        midi_val = TUNING[s_idx] + fret
        n = note.Note(midi=midi_val)
        # Randomize duration for playback variety 
        n.duration = duration.Duration(random.choice(NOTE_DURATIONS))
        p.append(n)
        
        # Console Output Construction
        # visual_lines[0] is High e (Index 5 in TUNING)
        # visual_lines[5] is Low E (Index 0 in TUNING)
        for i in range(6):
            if (5 - i) == s_idx: 
                visual_lines[i] += f"-{fret}-".ljust(4, '-')
            else: 
                visual_lines[i] += "----"
            
    s.append(p)
    
    # Print Tablature
    for line in visual_lines: 
        print(line)
    
    sp = midi.realtime.StreamPlayer(s)
    sp.play() 

if __name__ == "__main__":
    print("Evolutionary composition in progress...")
    best_song = genetic_algorithm()
    play_and_show(best_song)