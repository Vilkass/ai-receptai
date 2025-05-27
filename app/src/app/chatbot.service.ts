import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ChatbotService {
  private apiUrl = 'http://localhost:8000/ask';

  constructor(private http: HttpClient) { }

  askQuestion(
    question: string,
    chatHistory: string,
    file?: File | null
  ): Observable<{ question: string; answer: string }> {
    const formData = new FormData();

    // Append question and chat history
    formData.append('question', question);
    formData.append('history', chatHistory);

    // Append file if present
    if (file) {
      formData.append('file', file);
    }

    return this.http.post<{ question: string; answer: string }>(this.apiUrl, formData);
  }
}
