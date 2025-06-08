import { Client, Embed, EmbedBuilder, GatewayIntentBits } from "discord.js";
import type { Message, OmitPartialGroupDMChannel } from "discord.js";
import OpenAI from "openai";
import type {
  ChatCompletionAssistantMessageParam,
  ChatCompletionNamedToolChoice,
  ChatCompletionUserMessageParam,
} from "openai/resources/index";
import { z } from "zod";

const { DISCORD_TOKEN, AISTUDIO_API_KEY } = process.env;

let pongActive = false;

let pongTimeoutId: NodeJS.Timeout | null = null;
const pongTimeout = 60000;

// Early return/gate clause for missing token
if (!DISCORD_TOKEN) {
  throw new Error("Missing DISCORD_TOKEN in environment variables.");
}
if (!AISTUDIO_API_KEY) {
  throw new Error("Missing AISTUDIO_API_KEY in environment variables.");
}

const openai = new OpenAI({
  apiKey: AISTUDIO_API_KEY,
  baseURL: "https://generativelanguage.googleapis.com/v1beta/openai/",
});

const toolSchema = z.object({ name: z.string(), parameters: z.any() });

async function playAudio(name: string) {
  //play some audio
  console.debug("CALLED PLAY AUDIO", name);
}

async function stopAudio() {
  //stop audio
  console.debug("CALLED STOP AUDIO");
}

async function sleep() {
  console.debug("CALLED SLEEP");
  if (pongTimeoutId !== null) clearTimeout(pongTimeoutId);
  client.user?.setPresence({
    status: "idle",
  });
  pongActive = false;
}

const tools: Record<string, (parameters: any) => Promise<void>> = {
  play_audio: playAudio,
  stop_audio: stopAudio,
  sleep,
};

async function ai(
  messages: (
    | ChatCompletionUserMessageParam
    | ChatCompletionAssistantMessageParam
  )[]
) {
  const response = await openai.chat.completions.create({
    model: "gemma-3-27b-it",
    messages: [
      {
        role: "user",
        content: `You are an AI called Pong. Answer in a short conversational style. If I ask for something more extensive you should give longer answers.

You have access to functions. If you decide to invoke any of the function(s),
you MUST put it in the format of
{"name": function name, "parameters": dictionary of argument name and its value}

You SHOULD NOT include any other text in the response if you call a function
[
  {
    "name": "play_audio",
    "description": "Plays a song or youtube video by name. Only call this function if I explicitly ask you to.",
    "parameters": {
      "type": "object",
      "properties": {
        "name": {
          "type": "string",
          "description": "The title of the youtube video or song"
        }
      },
      "required": [
        "name"
      ]
    }
  },
  {
    "name": "stop_audio",
    "description": "Stops any audio that is currently playing. Only call this function if I explicitly ask you to.",
    "parameters": {
      "type": "object",
      "properties": {
      },
    }
  },
  {
    "name": "sleep",
    "description": "Makes you go to sleep. Do this if I ask you to leave in some way. eg 'go away', 'sleep', 'bye', 'goodbye'.",
    "parameters": {
      "type": "object",
      "properties": {
      },
    }
  }
]`,
      },
      ...messages,
    ],
  });
  return response.choices[0].message.content;
}

async function fetchHistory({
  message,
  limit = 20,
}: {
  message: OmitPartialGroupDMChannel<Message<boolean>>;
  limit?: number;
}) {
  const history = await message.channel.messages.fetch({ limit });
  const messages = history.map((msg) => {
    const functionCalls = msg.embeds
      .flatMap((embed) => embed.fields)
      .map((field) => field.value)
      .join("\n");
    return {
      role:
        msg.author.id === client.user?.id
          ? ("assistant" as const)
          : ("user" as const),
      content: `${msg.content}\n${functionCalls}`,
    };
  });
  return messages.reverse();
}

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent, // Required for accessing message content
  ],
});

client.once("ready", async () => {
  console.log(`Bot is ready! Logged in as ${client.user?.tag}`);
  client.user?.setPresence({
    status: "idle",
  });
});

client.on("messageCreate", async (message) => {
  console.info("received message:", message.content);
  // Avoid processing bot messages to prevent infinite loops
  if (message.author.bot) {
    return;
  }

  const messageContent = message.content.toLowerCase();

  if (
    messageContent.includes(" pong") ||
    messageContent.includes("pong ") ||
    messageContent === "pong"
  ) {
    pongActive = true;
    client.user?.setPresence({
      status: "online",
    });
  }
  if (!pongActive) {
    console.info("pong is inactive");
    return;
  }

  if (pongTimeoutId !== null) clearTimeout(pongTimeoutId);
  pongTimeoutId = setTimeout(() => {
    pongActive = false;
    client.user?.setPresence({
      status: "idle",
    });
  }, pongTimeout);

  const history = await fetchHistory({ message });
  console.debug({ history });

  await message.channel.sendTyping();
  const response = await ai([...history]);
  if (!response) return;

  const lines = response.split("\n");

  const normalLineIndices: number[] = [];

  const maybeFunctionCalls = lines.filter((line, index) => {
    try {
      JSON.parse(line);
      return true;
    } catch (error) {
      normalLineIndices.push(index);
      return false;
    }
  });
  const normalLines = normalLineIndices.map((index) => lines[index]);
  const responseWithoutFunctionCalls = normalLines.join("\n");

  let functionCallEmbeds: EmbedBuilder[] = [];

  maybeFunctionCalls.forEach(async (functionCallString) => {
    try {
      const functionCall = JSON.parse(functionCallString);
      const { name, parameters } =
        toolSchema.safeParse(functionCall).data ?? {};
      if (name === undefined) {
        console.error("failed to parse tool name:", functionCall);
        return;
      }
      const tool = tools[name];
      tool(parameters);
      functionCallEmbeds.push(
        new EmbedBuilder().addFields({
          name: "function call",
          value: functionCallString,
          inline: false,
        })
      );
    } catch (error) {
      console.error("failed to parse function call", error);
    }
  });

  message.channel.send({
    content: responseWithoutFunctionCalls,
    ...(functionCallEmbeds.length > 0 ? { embeds: functionCallEmbeds } : {}),
  });
});

client.login(DISCORD_TOKEN);
