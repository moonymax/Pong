import { Client, EmbedBuilder, GatewayIntentBits } from "discord.js";
import {
  joinVoiceChannel,
  createAudioPlayer,
  createAudioResource,
  VoiceConnection,
} from "@discordjs/voice";
import ytdl from "@distube/ytdl-core";
import yts from "yt-search";
import type { Message, OmitPartialGroupDMChannel } from "discord.js";
import OpenAI from "openai";
import type {
  ChatCompletionAssistantMessageParam,
  ChatCompletionUserMessageParam,
} from "openai/resources/index";
import { z } from "zod";

const { DISCORD_TOKEN, AISTUDIO_API_KEY } = process.env;

// Early return/gate clause for missing token
if (!DISCORD_TOKEN) {
  throw new Error("Missing DISCORD_TOKEN in environment variables.");
}
if (!AISTUDIO_API_KEY) {
  throw new Error("Missing AISTUDIO_API_KEY in environment variables.");
}

const pongActiveInGuild: Record<string, boolean> = {};
const pongTimeoutIdInGuild: Record<string, NodeJS.Timeout | null> = {};

const voiceConnectionsByGuild: Record<string, VoiceConnection[]> = {};

const pongTimeout = 60000;

const rickroll = "https://www.youtube.com/watch?v=dQw4w9WgXcQ";

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildVoiceStates,
  ],
});

const openai = new OpenAI({
  apiKey: AISTUDIO_API_KEY,
  baseURL: "https://generativelanguage.googleapis.com/v1beta/openai/",
});

const toolSchema = z.object({ name: z.string(), parameters: z.any() });

async function getVoiceChannelByMessage(message: Message) {
  const authorId = message.author.id;
  const maybeChannels = await message.guild?.channels.fetch();
  const voiceChannels = maybeChannels?.filter((channel) =>
    channel?.isVoiceBased()
  );
  if (!voiceChannels) return;
  const voiceChannelWithUser = voiceChannels.find((channel) =>
    channel?.members.some((member) => member.id === authorId)
  );
  if (!voiceChannelWithUser) return;

  return voiceChannelWithUser;
}

async function joinVoiceChannelTool(message: Message) {
  //join voice channel
}

async function leaveVoiceChannel(message: Message) {
  //leaving voice channel
}

async function playAudio(message: Message, { name }: { name: string }) {
  const guildId = message.guildId;
  if (!guildId) return;

  const voiceChannelWithUser = await getVoiceChannelByMessage(message);
  if (!voiceChannelWithUser) return;

  const connection = joinVoiceChannel({
    channelId: voiceChannelWithUser.id,
    guildId: voiceChannelWithUser.guild.id,
    adapterCreator: voiceChannelWithUser.guild.voiceAdapterCreator,
  });

  if (voiceConnectionsByGuild[guildId]) {
    voiceConnectionsByGuild[guildId].push(connection);
  } else {
    voiceConnectionsByGuild[guildId] = [connection];
  }

  const result = await yts(name);
  const url = result.videos[0].url;

  const audioPlayer = createAudioPlayer();

  const subscription = connection.subscribe(audioPlayer);

  if (subscription) {
    const stream = await ytdl(url, {
      quality: "highestaudio",
      filter: "audioonly",
    });
    audioPlayer.play(createAudioResource(stream));
  }
  audioPlayer.addListener("stateChange", (oldState, newState) => {
    console.debug("state changed to", newState.status);
    if (newState.status === "idle") {
      subscription?.unsubscribe();
      connection.destroy();
      audioPlayer.stop(true);
    }
  });
  console.debug("This is running right after starting to play");
}

async function stopAudio(message: Message) {
  const guildId = message.guildId;
  if (!guildId) return;
  const connections = voiceConnectionsByGuild[guildId];
  if (!connections) return;
  connections.forEach((connection) => {
    connection.disconnect();
    connection.destroy();
  });
}

async function sleep(message: Message) {
  const guildId = message.guildId;
  if (!guildId) return;

  const pongTimeoutId = pongTimeoutIdInGuild[guildId];
  if (pongTimeoutId !== null) clearTimeout(pongTimeoutId);
  client.user?.setPresence({
    status: "idle",
  });
  pongActiveInGuild[guildId] = false;
}

const tools: Record<
  string,
  (message: Message, parameters: any) => Promise<void>
> = {
  // join_voice_channel: joinVoiceChannelTool,
  // leave_voice_channel: leaveVoiceChannel,
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
${JSON.stringify([
  // {
  //   name: "join_voice_channel",
  //   description:
  //     "Allows you to join the voice channel of the user. Only call this function if I explicitly ask you to.",
  //   parameters: {
  //     type: "object",
  //     properties: {},
  //   },
  // },
  // {
  //   name: "leave_voice_channel",
  //   description:
  //     "Allows you to leave the voice channel of the user. Only call this function if I explicitly ask you to.",
  //   parameters: {
  //     type: "object",
  //     properties: {},
  //   },
  // },
  {
    name: "play_audio",
    description:
      "Plays a song or youtube video by name. Only call this function if I explicitly ask you to.",
    parameters: {
      type: "object",
      properties: {
        name: {
          type: "string",
          description: "The title of the youtube video or song",
        },
      },
      required: ["name"],
    },
  },
  {
    name: "stop_audio",
    description:
      "Stops any audio that is currently playing. Only call this function if I explicitly ask you to.",
    parameters: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "sleep",
    description:
      "Makes you go to sleep. Do this if I ask you to leave in some way. eg 'go away', 'sleep', 'bye', 'goodbye'.",
    parameters: {
      type: "object",
      properties: {},
    },
  },
])}`,
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

client.once("ready", async () => {
  console.log(`Bot is ready! Logged in as ${client.user?.tag}`);
  client.user?.setPresence({
    status: "idle",
  });
});

client.on("messageCreate", async (message) => {
  // Avoid processing bot messages to prevent infinite loops
  if (message.author.bot) {
    return;
  }

  const messageContent = message.content.toLowerCase();

  const guildId = message.guildId;

  // This prevents messaging pong in DMs
  if (!guildId) return;

  if (
    messageContent.includes(" pong") ||
    messageContent.includes("pong ") ||
    messageContent === "pong"
  ) {
    pongActiveInGuild[guildId] = true;
    client.user?.setPresence({
      status: "online",
    });
  }
  if (!pongActiveInGuild[guildId]) {
    console.info("pong is inactive");
    return;
  }

  if (pongTimeoutIdInGuild[guildId] !== null)
    clearTimeout(pongTimeoutIdInGuild[guildId]);
  pongTimeoutIdInGuild[guildId] = setTimeout(() => {
    pongActiveInGuild[guildId] = false;
    client.user?.setPresence({
      status: "idle",
    });
  }, pongTimeout);

  const history = await fetchHistory({ message });

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
      tool(message, parameters);
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
