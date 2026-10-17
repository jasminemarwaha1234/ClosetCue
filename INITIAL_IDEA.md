Main idea: Outfit-building shopping agent, Virtual try-on (“Clueless” closet), full outfit building instead of single items

Tracks targeted: Paper, Veri, GoDaddy

## Initial thought process

- What’s lacking in shopping:
  - You can’t tell how something looks on you until it arrives, so you guess and return it.
  - Stores sell items, but people think in outfits.
  - Comparing prices, sizes, and shipping across sites is tedious.
  - Checkout is where people drop off, and trust is the barrier.
  - https://shortandsweetfashion.substack.com/p/30-years-since-clueless-digital-closet
  - Access to camera roll so model can be trained on the clothes u have taken pics of wearing most often and its personalized that way (just have privacy concerns for camera roll) 
  - Don’t request full camera roll access. Have the user pick 10 to 20 photos of outfits they like or wear often with a normal photo picker. That avoids the permission problem and is easy to demo. Then tell judges how privacy works:
    - Photos are processed in-session and not stored.
    - The user chooses what is analyzed.
    - There is a one-tap “delete my data” button.

The product:
- Upload a photo and get a try-on preview of the item on you.
- The agent builds a full fit around it: shoes, accessories, layers, within your budget and style.
- It checks out securely, which is where Visa fits (tokenized payments, spending limits you set, and the agent never sees your card number).
- It’s easy to demo and visually impressive, which judges like.

Later features:
- makeup products based on skin type/skin tone

## Later reformed idea (prioritize this over above)

Frontend: 
	-Expo (React Native) phone app, with screens designed in Paper (https://paper.design/) first.
-Camera roll scan with a single permission prompt (expo-media-library), thumbnails via expo-image-manipulator.
-Screens: consent, scanning progress, “Your looks” review, pick item and budget, outfit cards, try-on view, checkout, fit feedback.
-A simple landing and privacy page on your GoDaddy domain.

Backend:
	-FastAPI
-Llama (open-source): reads photos, groups looks, writes the style profile. Also your baseline for the stylist.
-Veri-tuned stylist model: takes profile, budget, and anchor item, and returns an outfit from the catalog. Hosted Gemini or another LLM is the fallback.
-Try-on: a hosted try-on or image-editing model.
-Checkout: a Visa-style flow with spending limit, confirmation step, and tokenized-payment messaging. Simulated unless Visa gives you a sandbox.
-Endpoints: /scan, /profile, /outfits, /tryon, /checkout.
-Catalog: about 20 to 40 items in a JSON file with images AND/OR Supabase for database

Features:
- automatic camera roll scan sectioned into your usual looks AND/OR manually choose 10-20 photos if they don't want to connect their camera roll (give them a choice) 
- existing style profile based on uploaded photos
- full outfit searcher and builder within budget (looks at online resources, recommending based on your style profile)
- secure checkout via Visa with a spending limit and confirmation, a trust screen (what data is used, delete-my-data, AI use policy, merchant impact panel)
- “How did it fit?” feedback that updates your profile.
- AI try-on on your photo
- potential: sharing with friends
- potential: integration with social media
