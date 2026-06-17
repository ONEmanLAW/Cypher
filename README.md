# Cypher

> Learn beatboxing like a game. An interactive academy to master the fundamental sounds, one cypher at a time.

![Hero](public/readMeImg/hero.jpg)

BeatPath breaks down each sound (kick, hi-hat, snare…) into progressive exercises: you listen to the demo, study the technique, then it's your turn to play. Sounds unlock one by one, with a visual direction inspired by GBB battles.

## Sound Recognition

The core of the project: a Python model analyzes the audio captured from the mic and compares it to the target sound. It validates your attempts in real time and tells you whether your kick actually sounds like a kick. The backend exposes this model to the frontend for live feedback during exercises.

## Features

- Sound library with audio preview, even on locked sounds
- Video exercises split into phases (Intro, Demo, Technique, Attempts, Recap)
- Guided attempts: the video pauses, you reproduce the sound, the model evaluates it
- Gamified progression (locked / available / in progress / done)
- Vinyl transitions between screens

![Sound Select](public/readMeImg/sound-select.png)
![Exercises](public/readMeImg/exercises.png)
![Exercise N°6](public/readMeImg/exercise06.png)

## Stack

- **Frontend** : Vue 3 (`<script setup>`), Vue Router, Pinia
- **Backend** : Python (audio recognition model)
- **Runtime** : Bun
- Custom design system (orange / ink / bone, grain texture)

## Install

```sh
bun install
```

Then depending on your OS:

**Windows**
```sh
bun run server:setup:win
```

**Mac / Linux**
```sh
bun run server:setup:mac
```

## Run

In two separate terminals:

**Frontend**
```sh
bun run dev
```

**Backend**

Windows:
```sh
bun run server:win
```

Mac / Linux:
```sh
bun run server:mac
```
