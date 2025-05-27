import { ChangeDetectorRef, Component, ElementRef, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { registerLocaleData } from '@angular/common';
import localeLt from '@angular/common/locales/lt';
import { ChatbotService } from './chatbot.service';
import { marked } from 'marked';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

registerLocaleData(localeLt);

interface ChatMessage {
  text?: string;
  fileName?: string;
  file?: File;
  sender: 'user' | 'ai';
  timestamp: Date;
  feedback?: 'positive' | 'negative';
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, FormsModule, CommonModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  message: string = '';
  selectedFile: File | null = null;
  uploadedFile: File | null = null;
  conversationStart?: Date;
  messages: ChatMessage[] = [];

  loading = false;
  private shouldScroll = false;

  @ViewChild('chatMessages') chatMessagesRef!: ElementRef<HTMLDivElement>;
  @ViewChild('fileInputRef') fileInputRef!: ElementRef<HTMLInputElement>;
  @ViewChild('autosize') autosizeRef!: ElementRef<HTMLTextAreaElement>;


  constructor(private chatbot: ChatbotService, private sanitizer: DomSanitizer, private cdr: ChangeDetectorRef) { }

  hoveredIndex: number | null = null;
  hoveredAiIndex: number | null = null;

  ngAfterViewInit(): void {
    this.initNewConversation();
  }

  initNewConversation(): void {
    this.conversationStart = new Date();
    this.messages.push({
      text: 'Labas, aš esu išmanus AI agentas, gebantis padėti su el. receptų ir vaistų informacijos supratimu.\nĮkelk el. receptą **.pdf** formatu arba nukopijuok el. recepto **tekstą iš e.sveikatos portalo** ir aš tau padėsiu jį suprasti, bei atrasti vaistų alternatyvas.',
      sender: 'ai',
      timestamp: new Date()
    });
    }
  usePrompt(prompt: string): void {
    this.message = prompt;
  }


  onFileSelected(event: any): void {
    this.selectedFile = event.target.files[0];
  }

  onSubmit(): void {
    const trimmed = this.message.trim();
    if (!trimmed && !this.selectedFile) return;

    if (trimmed || this.selectedFile) {
      this.messages.push({
        text: trimmed,
        fileName: this.selectedFile?.name,
        file: this.selectedFile ?? undefined,
        sender: 'user',
        timestamp: new Date()
      });
      this.uploadedFile = this.selectedFile;
      this.shouldScroll = true;
      this.message = '';
      this.autoResizeTextArea(this.autosizeRef.nativeElement);

      this.loading = true;

    }

    if (this.selectedFile) {

      if (this.fileInputRef) {
        this.fileInputRef.nativeElement.value = '';
      }
      this.selectedFile = null;
    }
    // Dummy response
    // setTimeout(() => {

    //   this.loading = false;
    //   this.messages.push({
    //     text: 'Gavau jūsų žinutę. Netrukus atsakysiu!',
    //     sender: 'ai',
    //     timestamp: new Date()
    //   });

    //   this.shouldScroll = true;
    //   this.autoResizeTextArea(this.autosizeRef.nativeElement);
    // }, 1000);
    this.chatbot.askQuestion(trimmed, this.getChatHistory(), this.uploadedFile).subscribe({
      next: (res) => {
        this.messages.push({
          text: res.answer,
          sender: 'ai',
          timestamp: new Date()
        });
        this.cdr.detectChanges();
        this.loading = false;
        this.shouldScroll = true;
        this.autoResizeTextArea(this.autosizeRef.nativeElement);
      },
      error: (err) => {
        this.messages.push({
          text: '⚠️ Nepavyko gauti atsakymo.',
          sender: 'ai',
          timestamp: new Date()
        });
        this.loading = false;
        this.shouldScroll = true;
        this.autoResizeTextArea(this.autosizeRef.nativeElement);
      }
    });

  }


  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  scrollToBottom(): void {
    setTimeout(() => {
      const container = this.chatMessagesRef?.nativeElement;
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    });
  }

  onKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.onSubmit();
    }
  }

  autoResizeTextArea(textArea: HTMLTextAreaElement): void {
    textArea.rows = 1;
    const lineHeight = 24;
    const maxRows = 10;
    const scrollHeight = textArea.scrollHeight;
    const newRows = Math.min(Math.floor(scrollHeight / lineHeight), maxRows);
    textArea.rows = newRows;
  }
  getChatHistory(): string {
    return this.messages
      .slice(1)
      .map(msg => {
        const sender = msg.sender === 'user' ? 'User' : 'AI';
        const content = msg.text ? msg.text : msg.fileName ? `📎 ${msg.fileName}` : '';
        return `${sender}: ${content}`;
      })
      .join('\n');
  }
  onHoverAI(index: number) {
    this.hoveredAiIndex = index;
  }

  onFeedback(index: number, type: 'positive' | 'negative') {
    this.messages[index].feedback = type;
  }

  formatMarkdown(text: string): SafeHtml {
  const html = marked.parseInline(text);
  return this.sanitizer.bypassSecurityTrustHtml(html);
}

}
